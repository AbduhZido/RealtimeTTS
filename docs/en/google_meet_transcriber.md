# Google Meet Transcriber Architecture

[EN](../en/google_meet_transcriber.md) | [FR](../fr/google_meet_transcriber.md) | [ES](../es/google_meet_transcriber.md) | [DE](../de/google_meet_transcriber.md) | [IT](../it/google_meet_transcriber.md) | [ZH](../zh/google_meet_transcriber.md) | [JA](../ja/google_meet_transcriber.md) | [HI](../hi/google_meet_transcriber.md) | [KO](../ko/google_meet_transcriber.md) | [RU](../ru/google_meet_transcriber.md)

## Overview

This document describes the end-to-end architecture for real-time Google Meet transcription using a browser extension, RealtimeSTT relay, and N8N workflow automation. The system captures audio from Google Meet, transcribes it server-side, and stores transcripts in Google Drive.

## Architecture Overview

The complete pipeline consists of the following components:

```
┌──────────────────────────────────────────────────────────────┐
│ Google Meet (Browser)                                        │
│                                                              │
│  [Audio Capture] ──── (WebSocket)                          │
│       (PCM Stream)                                           │
└──────────────────────────────────────────────────────────────┘
         │
         │ WebSocket + PCM Audio
         │
         v
┌──────────────────────────────────────────────────────────────┐
│ Browser Extension                                            │
│                                                              │
│  [Listener] ────────► [WebSocket Client]                   │
│                       (Connect & Stream Handshake)          │
└──────────────────────────────────────────────────────────────┘
         │
         │ WebSocket + PCM Audio Frames
         │
         v
┌──────────────────────────────────────────────────────────────┐
│ Server (FastAPI + RealtimeSTT)                              │
│                                                              │
│  [WebSocket Handler] ──► [RealtimeSTT Engine]             │
│       │                       │                             │
│       │ Handshake             │ Text Output                 │
│       │ PCM Frames            │                             │
│       └───────────────────────┘                             │
│                                                              │
│  [Transcription Buffer] ──► [Webhook Dispatcher]           │
│       (Manages Streaming)      (POST to N8N)               │
└──────────────────────────────────────────────────────────────┘
         │
         │ HTTP/HTTPS POST
         │ JSON Webhook Payload
         │
         v
┌──────────────────────────────────────────────────────────────┐
│ N8N Workflow Automation                                      │
│                                                              │
│  [Webhook Receiver] ──► [Process Transcript]               │
│                          │                                   │
│                          ├─► [Google Drive Upload]         │
│                          └─► [Email Notification]          │
└──────────────────────────────────────────────────────────────┘
         │
         │ File Storage + Notifications
         │
         v
┌──────────────────────────────────────────────────────────────┐
│ Google Drive                                                 │
│                                                              │
│  [Transcript Files] (folder: Meeting_YYYYMMDD_HHMMSS)     │
└──────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Server-Side Transcription (Not Browser-Based)

**Decision**: Transcription runs in a dedicated FastAPI service wrapping RealtimeSTT, not inside the browser extension.

**Rationale**:
- **Resource Efficiency**: Transcription is computationally intensive; offloading to server saves browser memory/CPU
- **Flexibility**: Easy to upgrade transcription engines without browser extension updates
- **Model Management**: Server can manage large ML models without bloating the extension
- **Resilience**: Server can handle failures gracefully and retry transcription independently
- **Scalability**: Multiple browser extensions can connect to the same transcription service

### 2. WebSocket + PCM Streaming

**Decision**: Use WebSocket for bidirectional, low-latency streaming of PCM audio frames.

**Rationale**:
- **Low Latency**: WebSocket is faster than HTTP request-response for streaming
- **Persistent Connection**: Maintains session state without reconnect overhead
- **Binary Support**: PCM audio is binary data; WebSocket handles this efficiently
- **Backpressure**: Can implement flow control if browser sends faster than server processes

**PCM Format Specification**:
- **Sample Rate**: 16,000 Hz (RealtimeSTT requirement)
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit signed integer (PCM16)
- **Frame Size**: Typically 512–4,096 samples per frame (~32–256 ms at 16 kHz)
- **Endianness**: Little-endian

### 3. Webhook Payload Contract

**Decision**: Use HTTP POST webhooks to send transcribed text and metadata to N8N.

**Rationale**:
- **Decoupling**: Server and N8N are loosely coupled; either can be upgraded independently
- **Asynchronous**: Transcription completes independently of webhook delivery
- **Flexibility**: N8N can retry, filter, or route payloads based on metadata
- **Audit Trail**: Webhook logs provide a complete record of transcription events

**Security Considerations**:
- **HTTPS Only**: All webhook URLs must use HTTPS (TLS 1.2+)
- **API Key**: Include `X-API-Key` header in webhook requests for authentication
- **Payload Signature**: Optionally sign payloads with HMAC-SHA256 for integrity verification
- **Timeout**: Server should retry failed webhooks with exponential backoff (max 3 retries)

## Data Contracts

### 1. Browser Extension → Server (WebSocket)

#### Handshake Message (Client to Server)

When the browser extension starts a new transcription session:

```json
{
  "type": "start",
  "session_id": "meet-session-12345-67890",
  "meeting_id": "meet.google.com/abc-defg-hij",
  "user_id": "user@example.com",
  "timestamp": "2024-12-11T14:30:00.000Z",
  "config": {
    "language": "en",
    "model": "base",
    "enable_webhook": true
  }
}
```

**Fields**:
- `type`: Message type (`"start"`, `"audio"`, `"stop"`)
- `session_id`: Unique identifier for this transcription session (UUID v4 recommended)
- `meeting_id`: Google Meet meeting identifier (from URL or API)
- `user_id`: Email or ID of the extension user
- `timestamp`: ISO 8601 UTC timestamp of session start
- `config`: Optional transcription configuration
  - `language`: BCP 47 language code (e.g., `"en"`, `"de"`, `"fr"`)
  - `model`: RealtimeSTT model variant (`"base"`, `"tiny"`, `"small"`, etc.)
  - `enable_webhook`: Whether to send webhook notifications

#### Audio Frame Message (Client to Server)

Sent repeatedly while capturing audio:

```json
{
  "type": "audio",
  "session_id": "meet-session-12345-67890",
  "sequence_number": 1,
  "timestamp": "2024-12-11T14:30:01.512Z",
  "audio_data": "base64-encoded-pcm-bytes",
  "is_vad": true
}
```

**Fields**:
- `type`: Message type (`"audio"`)
- `session_id`: Must match the session from `start` message
- `sequence_number`: Monotonically increasing frame counter (detect packet loss)
- `timestamp`: ISO 8601 UTC timestamp when frame was captured
- `audio_data`: Base64-encoded PCM16 mono 16 kHz audio bytes
- `is_vad`: Voice Activity Detection flag (true if audio contains speech)

#### Stop Message (Client to Server)

Sent when transcription should terminate:

```json
{
  "type": "stop",
  "session_id": "meet-session-12345-67890",
  "timestamp": "2024-12-11T14:30:45.000Z",
  "reason": "user_stopped"
}
```

**Fields**:
- `type`: Message type (`"stop"`)
- `session_id`: Must match the session from `start` message
- `timestamp`: ISO 8601 UTC timestamp of stop time
- `reason`: Why transcription stopped (`"user_stopped"`, `"meeting_ended"`, `"connection_lost"`)

### 2. Server → N8N (HTTP Webhook)

#### Partial Transcript Webhook

Sent as transcription streams (for low-latency display):

```json
{
  "event": "transcript.partial",
  "session_id": "meet-session-12345-67890",
  "meeting_id": "meet.google.com/abc-defg-hij",
  "user_id": "user@example.com",
  "timestamp": "2024-12-11T14:30:10.234Z",
  "text": "Hello, this is a test",
  "confidence": 0.92,
  "language": "en",
  "duration_ms": 2500,
  "speaker_label": "speaker_0"
}
```

**Fields**:
- `event`: Webhook event type (`"transcript.partial"`)
- `session_id`: Transcription session identifier
- `meeting_id`: Google Meet identifier
- `user_id`: User who initiated the session
- `timestamp`: When this partial transcript was produced
- `text`: Partial transcribed text (may be incomplete sentence)
- `confidence`: Confidence score (0.0–1.0)
- `language`: Detected language code
- `duration_ms`: Milliseconds of audio processed so far
- `speaker_label`: Speaker identifier (for multi-speaker scenarios)

#### Final Transcript Webhook

Sent when transcription session completes:

```json
{
  "event": "transcript.final",
  "session_id": "meet-session-12345-67890",
  "meeting_id": "meet.google.com/abc-defg-hij",
  "user_id": "user@example.com",
  "timestamp": "2024-12-11T14:30:45.000Z",
  "text": "Hello, this is a test. It went well.",
  "confidence": 0.94,
  "language": "en",
  "total_duration_ms": 5000,
  "word_count": 8,
  "segments": [
    {
      "start_ms": 0,
      "end_ms": 2500,
      "text": "Hello, this is a test",
      "confidence": 0.92,
      "speaker_label": "speaker_0"
    },
    {
      "start_ms": 2500,
      "end_ms": 5000,
      "text": "It went well.",
      "confidence": 0.96,
      "speaker_label": "speaker_0"
    }
  ],
  "metadata": {
    "extension_version": "1.0.0",
    "server_version": "1.2.3",
    "processing_time_ms": 4200
  }
}
```

**Fields**:
- `event`: Webhook event type (`"transcript.final"`)
- `session_id`: Transcription session identifier
- `meeting_id`: Google Meet identifier
- `user_id`: User who initiated the session
- `timestamp`: When transcription completed
- `text`: Complete transcribed text of the entire session
- `confidence`: Overall confidence score (0.0–1.0)
- `language`: Detected language code
- `total_duration_ms`: Total milliseconds of audio captured
- `word_count`: Number of words in final transcript
- `segments`: Array of transcript segments (for fine-grained control)
  - `start_ms`: Segment start time in milliseconds
  - `end_ms`: Segment end time in milliseconds
  - `text`: Segment text
  - `confidence`: Segment confidence score
  - `speaker_label`: Speaker identifier
- `metadata`: Additional metadata
  - `extension_version`: Browser extension version
  - `server_version`: Transcription server version
  - `processing_time_ms`: Total server processing time

#### Error Webhook

Sent if transcription encounters an error:

```json
{
  "event": "transcript.error",
  "session_id": "meet-session-12345-67890",
  "meeting_id": "meet.google.com/abc-defg-hij",
  "user_id": "user@example.com",
  "timestamp": "2024-12-11T14:30:20.000Z",
  "error_code": "MODEL_LOAD_FAILED",
  "error_message": "Failed to load transcription model: CUDA out of memory",
  "partial_text": "Hello, this is"
}
```

**Fields**:
- `event`: Webhook event type (`"transcript.error"`)
- `session_id`: Transcription session identifier
- `meeting_id`: Google Meet identifier
- `user_id`: User who initiated the session
- `timestamp`: When the error occurred
- `error_code`: Machine-readable error code
- `error_message`: Human-readable error description
- `partial_text`: Any text transcribed before the error (if applicable)

## Security Considerations

### API Key Management

1. **Authentication**
   - Browser extension must include a valid API key in the WebSocket connection (e.g., as a query parameter or in an initial auth message)
   - Server validates the API key before accepting audio streams
   - API keys should be rotated regularly (at least quarterly)

2. **Key Storage**
   - Never hardcode API keys in browser extension code
   - Use browser's secure storage API (`chrome.storage.sync` or equivalent)
   - Key should be obtained from a secure server endpoint on first install

3. **Webhook Authentication**
   - All webhook URLs must use HTTPS (TLS 1.2 or higher)
   - Include `X-API-Key` header in webhook requests
   - N8N webhook URL should be kept secret; don't expose in client-side code
   - Validate webhook source using optional HMAC-SHA256 signatures

### Transport Security

1. **WebSocket (Browser → Server)**
   - Must use WSS (WebSocket Secure, TLS 1.2+)
   - Server certificate must be valid and trusted
   - Browser extension should reject unverified connections

2. **Webhooks (Server → N8N)**
   - Must use HTTPS (TLS 1.2+)
   - Server should verify N8N endpoint certificate
   - Retry failed webhooks with exponential backoff

### Data Privacy

1. **Audio Data**
   - Audio is transmitted encrypted over WSS
   - Server should not log raw audio or transcribed text longer than necessary
   - Consider end-to-end encryption if meeting participants require heightened privacy

2. **User Information**
   - `user_id` should not expose sensitive information (consider hashing or pseudonymization)
   - Meeting IDs in Google Meet URLs may be sensitive; consider anonymizing them

3. **Compliance**
   - Ensure compliance with local privacy regulations (GDPR, CCPA, etc.)
   - Provide users with a privacy notice before enabling transcription
   - Allow users to opt-out and delete transcripts

## Deployment Checklist

### Browser Extension
- [ ] API key is securely stored, never hardcoded
- [ ] WebSocket URI uses WSS (secure)
- [ ] Handshake includes all required fields
- [ ] Audio frames are properly base64-encoded
- [ ] `sequence_number` is monotonically increasing
- [ ] Stop message is sent on session termination

### Server
- [ ] API key validation is implemented
- [ ] WebSocket handlers validate all message fields
- [ ] RealtimeSTT engine is properly initialized with correct sample rate and format
- [ ] Webhook dispatcher retries failed requests
- [ ] Error handling and logging are in place
- [ ] CORS policy is configured correctly

### N8N Workflow
- [ ] Webhook URL is kept secret (not in client-side code)
- [ ] Payload signature validation is implemented (if using HMAC)
- [ ] File upload to Google Drive uses proper authentication
- [ ] Email notifications include sufficient context
- [ ] Error handling for missing Google Drive/email config

### General
- [ ] All communication uses HTTPS/WSS
- [ ] API keys and secrets are stored in environment variables
- [ ] Rate limiting is implemented to prevent abuse
- [ ] Audit logging is enabled for all webhook events
- [ ] Incident response plan is documented

## Integration with RealtimeSTT

The transcription server wraps RealtimeSTT with the following configuration:

```python
from RealtimeSTT import AudioToTextRecognizer

recognizer = AudioToTextRecognizer(
    model="base",
    language="en",
    sample_rate=16000,  # Must match browser extension
    chunk_size=1024,     # Adjust based on latency requirements
    initial_prompt="Transcribe a Google Meet conversation.",
    on_transcription_start=handle_start,
    on_transcription_stop=handle_stop
)

def handle_start():
    # Send partial transcript via webhook
    pass

def handle_stop():
    # Send final transcript via webhook
    pass

while audio_stream_is_active():
    pcm_data = receive_from_websocket()
    recognizer.feed_chunk(pcm_data)
```

The server should:
1. Accept WebSocket connections with session handshake
2. Feed PCM audio frames to RealtimeSTT in real-time
3. Capture transcription output and forward partial/final results via webhooks
4. Handle reconnections and graceful shutdown

## Troubleshooting

### WebSocket Connection Issues
- Verify WSS endpoint is accessible and certificate is valid
- Check API key is included and correctly formatted
- Ensure server is running and listening on the correct port
- Check firewall rules and proxy settings

### No Transcription Output
- Verify audio is being received (check server logs for incoming frames)
- Confirm sample rate is exactly 16 kHz
- Check RealtimeSTT model is loaded (watch for CUDA/memory errors)
- Enable detailed logging to see intermediate results

### Webhook Delivery Failures
- Verify N8N webhook URL is accessible and using HTTPS
- Check API key in webhook requests is correct
- Monitor N8N logs for incoming payloads
- Implement webhook retry with exponential backoff on server

### Audio Quality Issues
- Reduce frame size for lower latency (may increase overhead)
- Increase confidence threshold to filter low-quality results
- Try different RealtimeSTT model sizes
- Check for audio source noise; consider preprocessing

## References

- [RealtimeSTT Documentation](https://github.com/KoljaB/RealtimeSTT)
- [Google Meet API](https://developers.google.com/meet)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [N8N Documentation](https://docs.n8n.io/)
- [Google Drive API](https://developers.google.com/drive)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

