# Meet Transcriber - STT Relay Service

A WebSocket-based Speech-to-Text relay service for real-time meeting transcription.

## Features

- WebSocket endpoint for live audio ingestion from browser extensions
- Support for PCM audio (16kHz, 16-bit mono)
- Real-time transcription using RealtimeSTT
- Session management with configurable concurrent session limits
- Authentication support via bearer tokens
- Health check endpoint
- Structured logging
- Graceful shutdown
- Docker deployment support

## Installation

### From source

```bash
pip install -e ".[meet]"
```

## Configuration

Configuration can be provided via environment variables:

- `MEET_TRANSCRIBER_MODEL_NAME`: STT model name (default: `tiny.en`)
- `MEET_TRANSCRIBER_LANGUAGE`: Language code (default: `en`)
- `MEET_TRANSCRIBER_AUTH_TOKEN`: Optional authentication token
- `MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS`: Max concurrent sessions (default: `10`)
- `MEET_TRANSCRIBER_HOST`: Server host (default: `0.0.0.0`)
- `MEET_TRANSCRIBER_PORT`: Server port (default: `8765`)
- `MEET_TRANSCRIBER_LOG_LEVEL`: Logging level (default: `INFO`)

## Running

### Direct execution

```bash
python -m meet_transcriber.main
```

### Using uvicorn

```bash
uvicorn meet_transcriber.main:app --host 0.0.0.0 --port 8765
```

### Using Docker Compose

```bash
cd meet_transcriber
docker-compose up
```

## API Endpoints

### HTTP Endpoints

- `GET /` - Service information
- `GET /healthz` - Health check endpoint

### WebSocket Endpoint

- `WS /ws/transcribe` - Audio ingestion and transcription endpoint

## WebSocket Protocol

### Initialization

Client sends an initialization message:

```json
{
  "type": "init",
  "auth_token": "optional_bearer_token",
  "participant_info": {
    "user_id": "user123",
    "meeting_id": "meeting456"
  }
}
```

Server responds with:

```json
{
  "type": "ready",
  "session_id": "uuid",
  "model": "tiny.en",
  "language": "en"
}
```

### Audio Streaming

Client sends binary frames (PCM 16kHz, 16-bit mono):

```javascript
websocket.send(audioBuffer);
```

### Transcription Results

Server sends transcription updates:

```json
{
  "type": "transcript",
  "text": "transcribed text",
  "is_final": false,
  "session_id": "uuid"
}
```

### Stopping

Client sends stop message:

```json
{
  "type": "stop"
}
```

## Example Client

```python
import asyncio
import websockets
import json

async def transcribe():
    uri = "ws://localhost:8765/ws/transcribe"
    
    async with websockets.connect(uri) as websocket:
        # Initialize
        await websocket.send(json.dumps({
            "type": "init",
            "participant_info": {"user": "test"}
        }))
        
        # Wait for ready
        response = await websocket.recv()
        print(f"Ready: {response}")
        
        # Send audio data
        with open("audio.pcm", "rb") as f:
            while chunk := f.read(4096):
                await websocket.send(chunk)
                await asyncio.sleep(0.1)
        
        # Stop
        await websocket.send(json.dumps({"type": "stop"}))
        
        # Receive transcripts
        while True:
            try:
                message = await websocket.recv()
                print(f"Transcript: {message}")
            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(transcribe())
```

## Testing

```bash
pytest tests/test_meet_transcriber.py -v
```
