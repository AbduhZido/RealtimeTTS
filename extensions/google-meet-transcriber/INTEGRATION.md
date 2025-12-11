# Integration Guide: Extension + Relay Service

This document explains how the Google Meet Transcriber extension integrates with the meet_transcriber relay service.

## System Architecture

```
┌─────────────────────────────────────────┐
│         Google Meet (Browser)           │
│  ┌──────────────────────────────────┐   │
│  │   Chrome Meet Transcriber        │   │
│  │   Extension                      │   │
│  │                                  │   │
│  │  ┌──────────────────────────┐    │   │
│  │  │ Content Script (UI)      │    │   │
│  │  │ - Toggle button          │    │   │
│  │  │ - Status indicator       │    │   │
│  │  │ - Transcript display     │    │   │
│  │  └──────────────────────────┘    │   │
│  │                ↕                   │   │
│  │        chrome.runtime.sendMessage │   │
│  │                ↕                   │   │
│  │  ┌──────────────────────────┐    │   │
│  │  │ Background Service Worker│    │   │
│  │  │ - Audio capture          │    │   │
│  │  │ - Web Audio API          │    │   │
│  │  │ - WebSocket client       │    │   │
│  │  └──────────────────────────┘    │   │
│  │                ↕                   │   │
│  │        Chrome tabCapture API      │   │
│  └──────────────────────────────────┘   │
│                ↕                         │
│  ┌─────────────────────────────────┐    │
│  │ Web Audio API                   │    │
│  │ - Resample audio to 16kHz       │    │
│  │ - Convert to PCM 16-bit mono    │    │
│  └─────────────────────────────────┘    │
│                ↕                         │
│        WebSocket (binary frames)        │
└─────────────────────────────────────────┘
                 ↕
        ┌─────────────────────┐
        │ HTTP/WebSocket      │
        │ Network             │
        └─────────────────────┘
                 ↕
┌─────────────────────────────────────────┐
│   Meet Transcriber Relay Service        │
│   (FastAPI + RealtimeSTT)               │
│                                         │
│   POST http://localhost:8000            │
│   GET  http://localhost:8000/healthz    │
│   WS   ws://localhost:8000/ws/transcribe│
│                                         │
│  ┌──────────────────────────────────┐   │
│  │ WebSocket Handler                │   │
│  │ - Accept init message            │   │
│  │ - Queue audio frames             │   │
│  │ - Send transcript updates        │   │
│  └──────────────────────────────────┘   │
│                ↕                         │
│  ┌──────────────────────────────────┐   │
│  │ AudioTranscriber                 │   │
│  │ - RealtimeSTT integration        │   │
│  │ - Real-time transcription        │   │
│  │ - Speech/silence detection       │   │
│  └──────────────────────────────────┘   │
│                ↕                         │
│  ┌──────────────────────────────────┐   │
│  │ Optional: N8N Webhook Delivery   │   │
│  │ - Buffer transcript segments     │   │
│  │ - POST to N8N webhook            │   │
│  │ - Retry with exponential backoff │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Data Flow

### 1. User Clicks "Start Transcription"

**In Extension (content.js):**
```javascript
chrome.runtime.sendMessage({
  action: 'startCapture',
  relayUrl: 'ws://localhost:8000',
  language: 'en'
});
```

**In Extension (background.js):**
- Requests audio capture via `chrome.tabCapture.capture()`
- Initializes Web Audio API context (16kHz sample rate)
- Creates ScriptProcessorNode for audio processing
- Connects audio pipeline: `source → scriptProcessor → destination`
- Creates WebSocket connection to relay service

### 2. Relay Service Receives Connection

**WebSocket Init Handshake:**

Extension sends:
```json
{
  "type": "init",
  "language": "en",
  "participant_info": {
    "meeting_id": "meet_abc123",
    "meeting_title": "My Meeting"
  }
}
```

Relay service responds:
```json
{
  "type": "ready",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "base",
  "language": "en"
}
```

### 3. Audio Streaming

**Every 256ms (~4096 samples at 16kHz):**

Extension sends binary WebSocket frame containing Int16Array buffer:
```
Frame: Binary buffer [sample1, sample2, ...sample4096]
Each sample: 16-bit signed integer (-32768 to 32767)
Sample rate: 16kHz
Channels: 1 (mono)
Bit depth: 16 bits
```

**Relay service:**
- Receives binary frame via WebSocket
- Queues audio to `session.audio_queue`
- AudioTranscriber processes chunks incrementally
- Sends transcriptions back:
```json
{
  "type": "transcript",
  "text": "Hello world",
  "is_final": false,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 4. User Clicks "Stop Transcription"

Extension sends:
```json
{"type": "stop"}
```

**Cleanup:**
1. Extension stops audio capture: `mediaStreamTrack.stop()`
2. Closes Web Audio API context
3. Closes WebSocket connection
4. Relay service ends session and cleans up resources
5. If N8N webhook configured, sends final transcript

## WebSocket Message Protocol

### Extension → Relay Service

**1. Init (Once at start)**
```json
{
  "type": "init",
  "language": "en",
  "participant_info": {
    "meeting_id": "...",
    "meeting_title": "..."
  },
  "n8n_webhook_url": "https://..." // optional
}
```

**2. Audio (Binary frames, continuous)**
```
WebSocket.send(Int16Array.buffer)
```

**3. Stop (Once at end)**
```json
{"type": "stop"}
```

### Relay Service → Extension

**1. Ready (After init)**
```json
{
  "type": "ready",
  "session_id": "uuid",
  "model": "base",
  "language": "en"
}
```

**2. Transcript (Multiple, as available)**
```json
{
  "type": "transcript",
  "text": "Spoken text segment",
  "is_final": true/false,
  "session_id": "uuid"
}
```

**3. Error (If something goes wrong)**
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Audio Processing Pipeline (Extension)

```
Chrome Meet Audio Stream
         ↓
chrome.tabCapture.capture()
         ↓
MediaStreamSource (AudioContext)
         ↓
ScriptProcessorNode (4096 samples, 16kHz)
         ↓
JavaScript callback: onaudioprocess
         ↓
convertToPCM16(floatArray)
  - Input: Float32Array [-1.0 to 1.0]
  - Output: Int16Array [-32768 to 32767]
         ↓
WebSocket.send(pcmBuffer)
         ↓
Relay Service receives binary frame
         ↓
AudioQueue
         ↓
RealtimeSTT (continuous transcription)
```

## Configuration

### Extension Settings (chrome.storage.sync)

```javascript
{
  "relayUrl": "ws://localhost:8000",  // WebSocket endpoint
  "language": "en"                     // ISO 639-1 language code
}
```

Users configure via:
1. Right-click extension icon
2. Select "Options"
3. Update "Relay Service URL" and "Language"
4. Click "Save Settings"

Settings auto-sync across Chrome devices (via chrome.storage.sync).

### Relay Service Configuration

Environment variables (see `meet_transcriber/config.py`):

```bash
# Core
MEET_TRANSCRIBER_HOST=0.0.0.0
MEET_TRANSCRIBER_PORT=8000
MEET_TRANSCRIBER_MODEL_NAME=base
MEET_TRANSCRIBER_LANGUAGE=en

# Session management
MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS=10
MEET_TRANSCRIBER_SESSION_TIMEOUT=3600

# N8N webhook (optional)
MEET_TRANSCRIBER_N8N_WEBHOOK_URL=https://...
MEET_TRANSCRIBER_N8N_MAX_RETRIES=3
MEET_TRANSCRIBER_N8N_RETRY_DELAY=1.0
MEET_TRANSCRIBER_N8N_TIMEOUT=30.0

# Logging
MEET_TRANSCRIBER_LOG_LEVEL=info
```

## Running the System

### 1. Start Relay Service

```bash
# Install dependencies
pip install -e ".[meet]"

# Start service
python -m meet_transcriber.main

# Or with Docker
cd meet_transcriber
docker-compose up
```

Service runs on `ws://localhost:8000` (WebSocket)

### 2. Load Extension in Chrome

```
1. chrome://extensions/
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select extensions/google-meet-transcriber/ folder
```

### 3. Configure Extension (Optional)

```
1. Right-click extension icon
2. Select "Options"
3. Set relay URL (must match step 1)
4. Select language
5. Click "Save"
```

### 4. Use in Google Meet

```
1. Open https://meet.google.com
2. Start or join a meeting
3. Click "Start Transcription" (top-right)
4. Speak naturally, transcriptions appear below the button
5. Click "Stop Transcription" when done
```

## Error Handling

### Extension Fails to Connect

**Symptoms:** Button shows error message in red

**Troubleshooting:**
1. Verify relay service is running: `curl http://localhost:8000/healthz`
2. Check extension options: relay URL matches service URL
3. Check browser console (F12) for detailed errors
4. Try reloading page

### No Audio Being Captured

**Symptoms:** Status shows "Recording" but no transcriptions appear

**Troubleshooting:**
1. Check relay service logs for audio frames
2. Verify microphone is working on the Meet page
3. Check WebSocket connection in DevTools (Network → WS)
4. Try reloading the extension

### Relay Service Not Receiving Audio

**Symptoms:** Extension says "Recording" but relay shows no audio queue activity

**Troubleshooting:**
1. Check relay health: `curl http://localhost:8000/healthz`
2. Check relay logs for session creation: `Session created`
3. Verify WebSocket connection is successful
4. Check audio format: must be 16kHz, 16-bit mono PCM

## Testing

### Simulate Extension Behavior

```bash
cd extensions/google-meet-transcriber
npm install ws  # or use: python -m pip install websockets

# Run test
node test-extension.js

# Expected output:
# [Test] Starting extension simulator...
# [Extension] Connected to relay service
# [Extension] Sending init message...
# [Extension] Ready! Session ID: ...
# [Extension] Sending test audio (48 chunks of 4096 samples)
# [Extension] Transcript: "..." (final: true)
# [Extension] Sending stop message
# [Test] Complete!
```

### Monitor Relay Service

```bash
# Check active sessions
curl http://localhost:8000/healthz

# Example response:
# {
#   "status": "healthy",
#   "active_sessions": 1,
#   "max_sessions": 10
# }
```

## Performance Notes

- **Latency**: 200-500ms typical (network + processing)
- **Audio Quality**: 16kHz samples adequate for speech recognition
- **Memory**: ~20-50MB per active session
- **Bandwidth**: ~32kbps (16kHz × 16-bit × 1 channel)
- **CPU**: ~5-15% per active session (depends on model)

## Debugging

### Enable Detailed Logging

**Extension (Chrome DevTools):**
- Open DevTools (F12)
- Go to Console tab
- Watch for messages prefixed with `[Extension]` or `[Test]`
- Go to Network → WS to see WebSocket connection details

**Relay Service:**
```bash
# Set log level
MEET_TRANSCRIBER_LOG_LEVEL=debug python -m meet_transcriber.main

# Watch logs
tail -f /var/log/meet_transcriber.log
```

### WebSocket Inspection

**In Chrome DevTools:**
1. Open Network tab
2. Filter by "WS" (WebSocket)
3. Click the `/ws/transcribe` connection
4. View "Messages" to see init/transcript/stop messages

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Connect failed" | Relay service not running | Start service: `python -m meet_transcriber.main` |
| No transcriptions | Wrong relay URL | Check options page, verify URL matches service |
| Stuttering audio | Network congestion | Reduce other network usage |
| High latency | Slow computer | Close other applications, upgrade hardware |
| Crashes | Browser out of memory | Use smaller audio buffers or fewer concurrent sessions |

## Future Enhancements

- [ ] AudioWorklet for better performance
- [ ] Stereo/surround audio support
- [ ] Multi-speaker identification
- [ ] Speaker stats/analytics
- [ ] Transcript search/export
- [ ] Session replay
- [ ] Cloud storage integration
