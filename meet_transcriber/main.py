import asyncio
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.responses import JSONResponse

from meet_transcriber.config import settings
from meet_transcriber.session_manager import SessionManager
from meet_transcriber.transcriber import AudioTranscriber
from meet_transcriber.n8n_client import N8NWebhookClient
from meet_transcriber.transcript_buffer import TranscriptBuffer

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

session_manager: SessionManager = None
active_transcribers: Dict[UUID, AudioTranscriber] = {}
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global session_manager
    
    logger.info("Starting meet_transcriber service")
    logger.info(f"Configuration: model={settings.model_name}, language={settings.language}")
    logger.info(f"Max concurrent sessions: {settings.max_concurrent_sessions}")
    
    session_manager = SessionManager(max_concurrent_sessions=settings.max_concurrent_sessions)
    
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    logger.info("Shutting down meet_transcriber service")
    shutdown_event.set()
    cleanup_task.cancel()
    
    for session_id, transcriber in list(active_transcribers.items()):
        try:
            await transcriber.stop()
        except Exception as e:
            logger.error(f"Error stopping transcriber for session {session_id}: {e}")
    
    active_transcribers.clear()


app = FastAPI(
    title="Meet Transcriber STT Relay",
    description="WebSocket-based STT relay service for real-time meeting transcription",
    version="0.1.0",
    lifespan=lifespan,
)


async def periodic_cleanup():
    while not shutdown_event.is_set():
        try:
            await asyncio.sleep(60)
            if session_manager:
                await session_manager.cleanup_inactive_sessions()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


def verify_auth_token(authorization: str = Header(None)) -> bool:
    if settings.auth_token is None:
        return True
    
    if authorization is None:
        return False
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        return token == settings.auth_token
    
    return False


async def send_transcript_to_webhook(
    session_id: UUID,
    participant_info: Dict,
    transcript_buffer: TranscriptBuffer,
    n8n_client: Optional[N8NWebhookClient],
) -> bool:
    """Send transcript buffer to N8N webhook if configured."""
    if not n8n_client or not n8n_client.webhook_url:
        return False
    
    try:
        payload = {
            "meeting_metadata": {
                "session_id": str(session_id),
                "participants": participant_info.get("participants", []),
                "meeting_id": participant_info.get("meeting_id"),
                "meeting_title": participant_info.get("meeting_title"),
                "language": settings.language,
                "start_time": transcript_buffer.created_at.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
            },
            "transcript": {
                "full": transcript_buffer.get_full_transcript(),
                "segments": transcript_buffer.get_all_segments(),
            },
            "delivery_status": "pending",
        }
        
        result = await n8n_client.send_payload(payload)
        if result:
            payload["delivery_status"] = "delivered"
        return result
    except Exception as e:
        logger.error(f"Error preparing webhook payload: {e}")
        return False


@app.get("/healthz")
async def health_check():
    active_count = await session_manager.get_active_session_count() if session_manager else 0
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "active_sessions": active_count,
            "max_sessions": settings.max_concurrent_sessions,
        },
    )


@app.get("/")
async def root():
    return {
        "service": "meet_transcriber",
        "version": "0.1.0",
        "endpoints": {
            "websocket": "/ws/transcribe",
            "health": "/healthz",
        },
    }


@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()
    
    session = None
    transcriber = None
    transcription_task = None
    transcript_buffer = TranscriptBuffer()
    n8n_client: Optional[N8NWebhookClient] = None
    
    try:
        init_message = await websocket.receive_json()
        
        if init_message.get("type") != "init":
            await websocket.send_json({
                "type": "error",
                "message": "First message must be of type 'init'",
            })
            await websocket.close(code=1008)
            return
        
        auth_header = init_message.get("auth_token")
        if settings.auth_token and auth_header != settings.auth_token:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid authentication token",
            })
            await websocket.close(code=1008)
            return
        
        participant_info = init_message.get("participant_info", {})
        n8n_webhook_url = init_message.get("n8n_webhook_url")
        
        session = await session_manager.create_session(participant_info)
        
        logger.info(f"WebSocket connected for session {session.session_id}")
        
        if n8n_webhook_url or settings.n8n_webhook_url:
            webhook_url = n8n_webhook_url or settings.n8n_webhook_url
            n8n_client = N8NWebhookClient(
                webhook_url=webhook_url,
                max_retries=settings.n8n_max_retries,
                retry_delay=settings.n8n_retry_delay,
                timeout=settings.n8n_timeout,
            )
            logger.info(f"N8N webhook client configured for session {session.session_id}")
        
        async def send_transcript(text: str, is_final: bool):
            try:
                transcript_buffer.add_segment(text, is_final)
                await websocket.send_json({
                    "type": "transcript",
                    "text": text,
                    "is_final": is_final,
                    "session_id": str(session.session_id),
                })
            except Exception as e:
                logger.error(f"Error sending transcript: {e}")
        
        transcriber = AudioTranscriber(
            model_name=settings.model_name,
            language=settings.language,
            on_transcript=lambda text, is_final: asyncio.create_task(send_transcript(text, is_final)),
        )
        
        active_transcribers[session.session_id] = transcriber
        
        transcription_task = asyncio.create_task(
            transcriber.process_audio_queue(session.audio_queue)
        )
        
        await websocket.send_json({
            "type": "ready",
            "session_id": str(session.session_id),
            "model": settings.model_name,
            "language": settings.language,
        })
        
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_data = message["bytes"]
                
                if len(audio_data) > 0:
                    await session.audio_queue.put(audio_data)
                    await session_manager.update_activity(session.session_id)
                    
            elif "text" in message:
                try:
                    msg_data = json.loads(message["text"])
                    
                    if msg_data.get("type") == "stop":
                        logger.info(f"Received stop message for session {session.session_id}")
                        break
                        
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON text message")
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session.session_id if session else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass
    finally:
        if session and transcript_buffer.has_final_segments() and n8n_client:
            try:
                await send_transcript_to_webhook(
                    session.session_id,
                    session.participant_info,
                    transcript_buffer,
                    n8n_client,
                )
            except Exception as e:
                logger.error(f"Error sending transcript to webhook: {e}")
        
        if session:
            try:
                await session_manager.end_session(session.session_id)
            except Exception as e:
                logger.error(f"Error ending session: {e}")
        
        if transcriber:
            try:
                await transcriber.stop()
                if session and session.session_id in active_transcribers:
                    del active_transcribers[session.session_id]
            except Exception as e:
                logger.error(f"Error stopping transcriber: {e}")
        
        if transcription_task:
            try:
                transcription_task.cancel()
                await transcription_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error cancelling transcription task: {e}")
        
        try:
            await websocket.close()
        except:
            pass


def handle_shutdown(signum, frame):
    logger.info(f"Received signal {signum}, initiating shutdown")
    shutdown_event.set()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
