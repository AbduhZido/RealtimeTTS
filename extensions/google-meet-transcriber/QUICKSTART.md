# Google Meet Transcriber Extension - Quick Start

A minimal Chrome extension for real-time audio capture and transcription from Google Meet meetings.

## Installation (5 minutes)

### Step 1: Start the Relay Service

```bash
# From project root
pip install -e ".[meet]"
python -m meet_transcriber.main
```

Service runs on `http://localhost:8000` (WebSocket at `ws://localhost:8000/ws/transcribe`)

### Step 2: Load Extension in Chrome

1. Open `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Navigate to `extensions/google-meet-transcriber/` folder
5. Click **Open**

The extension should now appear in your extensions list.

### Step 3: Configure Settings (Optional)

1. Right-click the extension icon in Chrome toolbar
2. Click **Options**
3. Update settings if needed:
   - **Relay Service URL**: Default `ws://localhost:8000` (change if running elsewhere)
   - **Language**: Default English (select your language)
4. Click **Save Settings**

## Usage

### To Record a Meeting

1. Open `https://meet.google.com` and start or join a meeting
2. Look for **Meet Transcriber** panel in top-right corner
3. Click **Start Transcription**
4. Status will change to "Recording" with a red indicator
5. Speak naturally - transcriptions appear in real-time below the button
6. Click **Stop Transcription** to end recording

### Expected Output

You should see:
- **Recording Status**: Red dot with "Recording" text
- **Live Transcriptions**: Segments appear in the panel as you speak
- **Final Segments**: Green background indicates complete sentences
- **Partial Segments**: Orange background indicates ongoing speech

## Troubleshooting

### Extension Not Showing

**Problem**: No "Meet Transcriber" panel appears on Google Meet

**Solution**:
1. Verify you're on `https://meet.google.com` (not google.com/meet)
2. Refresh the page
3. Check `chrome://extensions/` - extension should be enabled (blue toggle)
4. Try reloading the extension

### Connection Failed

**Problem**: Red error message when clicking Start

**Solution**:
1. Verify relay service is running:
   ```bash
   curl http://localhost:8000/healthz
   # Should return: {"status":"healthy",...}
   ```
2. Check extension options - relay URL must match service URL
3. If service is on different machine, update relay URL in options
4. Check browser console (F12) for detailed errors

### No Transcriptions Appearing

**Problem**: Extension says "Recording" but no text appears

**Solution**:
1. Check microphone is working in Meet (audio levels should move)
2. Speak clearly and wait a moment for transcription
3. Check relay service logs for errors
4. Try reloading the page and starting again

## File Structure

```
extensions/google-meet-transcriber/
├── manifest.json              # Chrome extension configuration
├── background.js              # Audio capture & WebSocket client
├── content.js                 # UI injection & message relay
├── options.html               # Settings page UI
├── options.js                 # Settings page logic
├── README.md                  # Full documentation
├── INTEGRATION.md             # Architecture & protocol details
├── QUICKSTART.md              # This file
└── test-extension.js          # Test/simulation script
```

## How It Works

```
Google Meet Audio
       ↓
   chrome.tabCapture.capture()
       ↓
   Web Audio API (16kHz PCM conversion)
       ↓
   WebSocket binary frames
       ↓
   Relay Service (/ws/transcribe)
       ↓
   RealtimeSTT (transcription)
       ↓
   JSON transcript messages
       ↓
   Display in extension UI
```

## Technical Details

### Audio Format
- **Sample Rate**: 16 kHz
- **Bit Depth**: 16-bit signed
- **Channels**: Mono
- **Codec**: Raw PCM
- **Frame Size**: 4096 samples (~256ms)

### WebSocket Protocol

**Init Message** (sent once on start):
```json
{
  "type": "init",
  "language": "en",
  "participant_info": {
    "meeting_id": "auto_generated",
    "meeting_title": "Google Meet"
  }
}
```

**Audio Frames** (binary, continuous):
```
WebSocket.send(Int16Array.buffer)
```

**Stop Message** (sent on stop):
```json
{"type": "stop"}
```

**Transcript Messages** (received continuously):
```json
{
  "type": "transcript",
  "text": "Hello world",
  "is_final": true,
  "session_id": "uuid"
}
```

## Features

✅ Real-time audio capture from Google Meet
✅ Live transcription display
✅ Configurable relay service URL
✅ Multi-language support
✅ Status indicators (idle/recording/error)
✅ Automatic settings persistence
✅ Error handling & recovery
✅ Pure JavaScript (no build process)

## Limitations

- Chrome only (not Firefox)
- Single recording session per browser
- Requires relay service to be running
- Audio from Meet tab only (not system audio)
- Network latency affects transcription delay

## Advanced Configuration

### Custom Relay Service

To connect to a relay service on a different host:

1. Open extension options
2. Change "Relay Service URL" to your service URL
3. Must be WebSocket URL (ws:// or wss://)
4. Click "Save Settings"

### Running Relay Service on Different Machine

```bash
# On remote machine
MEET_TRANSCRIBER_HOST=0.0.0.0 python -m meet_transcriber.main

# In extension options, set URL to:
# ws://remote-ip:8000
```

### Secure Connection (WSS)

For production, use secure WebSocket:

```bash
# Relay service with SSL
MEET_TRANSCRIBER_HOST=0.0.0.0 MEET_TRANSCRIBER_SSL_CERT=/path/cert.pem MEET_TRANSCRIBER_SSL_KEY=/path/key.pem python -m meet_transcriber.main

# In extension options, set URL to:
# wss://your-domain.com:8000
```

## Testing

### Simulate Extension Behavior

```bash
# Requires Node.js with 'ws' package
npm install ws

# Run test
node extensions/google-meet-transcriber/test-extension.js

# Expected output:
# [Extension] Connected to relay service
# [Extension] Sending init message...
# [Extension] Ready! Session ID: ...
# [Extension] Sending test audio...
# [Extension] Transcript: "..." (final: true)
# [Extension] Complete!
```

## Performance

- **Memory**: ~20-50MB per active recording
- **CPU**: ~5-15% per recording
- **Bandwidth**: ~32kbps (16kHz × 16-bit × 1 channel)
- **Latency**: 200-500ms typical

## Next Steps

1. Start using the extension to transcribe meetings
2. Check relay service logs for transcription quality
3. Adjust language setting if needed
4. Experiment with different relay service configurations

## Support

For issues or questions:

1. Check this document's Troubleshooting section
2. Review detailed documentation in `README.md` and `INTEGRATION.md`
3. Check browser console (F12 → Console tab) for error messages
4. Verify relay service is running: `curl http://localhost:8000/healthz`

## License

Same as RealtimeTTS project
