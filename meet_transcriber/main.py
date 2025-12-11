import asyncio
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Optional
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.responses import JSONResponse

from meet_transcriber.config import settings
from meet_transcriber.session_manager import SessionManager
from meet_transcriber.transcriber import AudioTranscriber
from meet_transcriber.transcript_buffer import TranscriptBuffer
from meet_transcriber.n8n_client import N8NWebhookClient

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
    
    # Log N8N webhook configuration
    if settings.n8n_webhook_enabled and settings.n8n_webhook_url:
        logger.info(f"N8N Webhook enabled: {settings.n8n_webhook_url}")
        logger.info(f"  - Max retries: {settings.n8n_max_retries}")
        logger.info(f"  - Retry delay: {settings.n8n_retry_delay}s")
        logger.info(f"  - Backoff factor: {settings.n8n_backoff_factor}")
        logger.info(f"  - Timeout: {settings.n8n_timeout}s")
        logger.info(f"  - Flush interval: {settings.transcript_flush_interval}s")
        logger.info(f"  - Max segments before flush: {settings.transcript_max_segments_before_flush}")
    else:
        logger.info("N8N Webhook: disabled")
    
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
    transcript_buffer = None
    n8n_client = None
    
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
        meeting_metadata = init_message.get("meeting_metadata", {})
        webhook_url = init_message.get("webhook_url", settings.n8n_webhook_url)
        enable_webhook = init_message.get("enable_webhook", settings.n8n_webhook_enabled)
        
        session = await session_manager.create_session(participant_info)
        
        logger.info(f"WebSocket connected for session {session.session_id}")
        
        # Prepare meeting metadata
        full_meeting_metadata = {
            "session_id": str(session.session_id),
            "title": meeting_metadata.get("title", "Untitled Meeting"),
            "participants": participant_info,
            "language": settings.language,
            "model": settings.model_name,
            "start_time": session.created_at.isoformat() + "Z",
            "webhook_enabled": enable_webhook and bool(webhook_url),
            **meeting_metadata,
        }
        
        # Setup N8N webhook if enabled
        if enable_webhook and webhook_url:
            try:
                n8n_client = N8NWebhookClient(
                    webhook_url=webhook_url,
                    max_retries=settings.n8n_max_retries,
                    retry_delay=settings.n8n_retry_delay,
                    backoff_factor=settings.n8n_backoff_factor,
                    timeout=settings.n8n_timeout,
                )
                logger.info(f"N8N webhook client initialized for session {session.session_id}")
            except Exception as e:
                logger.error(f"Failed to initialize N8N webhook client: {e}")
                # Continue without webhook functionality
                enable_webhook = False
        
        # Create transcript buffer
        if enable_webhook and n8n_client:
            transcript_buffer = TranscriptBuffer(
                session_id=session.session_id,
                meeting_metadata=full_meeting_metadata,
                flush_interval=settings.transcript_flush_interval,
                max_segments_before_flush=settings.transcript_max_segments_before_flush,
            )
            logger.info(f"Transcript buffer created for session {session.session_id}")
        
        async def send_transcript(text: str, is_final: bool):
            try:
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
            transcript_buffer=transcript_buffer,
            n8n_client=n8n_client,
            meeting_metadata=full_meeting_metadata,
        )
        
        active_transcribers[session.session_id] = transcriber
        
        transcription_task = asyncio.create_task(
            transcriber.process_audio_queue(session.audio_queue)
        )
        
        # Send ready message with additional info
        ready_message = {
            "type": "ready",
            "session_id": str(session.session_id),
            "model": settings.model_name,
            "language": settings.language,
            "webhook_enabled": enable_webhook and n8n_client is not None,
            "buffer_config": {
                "flush_interval": settings.transcript_flush_interval,
                "max_segments_before_flush": settings.transcript_max_segments_before_flush,
            } if transcript_buffer else None,
        }
        
        if settings.enable_webhook_delivery_status:
            ready_message["enable_delivery_status"] = True
        
        await websocket.send_json(ready_message)
        
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
                    
                    elif msg_data.get("type") == "get_webhook_status" and settings.enable_webhook_delivery_status:
                        if n8n_client:
                            delivery_status = n8n_client.get_delivery_status(str(session.session_id))
                            await websocket.send_json({
                                "type": "webhook_status",
                                "session_id": str(session.session_id),
                                "delivery_status": delivery_status,
                            })
                        
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
        # Send final webhook delivery status if enabled
        final_webhook_status = None
        if transcriber and settings.enable_webhook_delivery_status:
            try:
                # Get the final webhook delivery status
                if n8n_client:
                    final_webhook_status = n8n_client.get_delivery_status(str(session.session_id) if session else "unknown")
                    await websocket.send_json({
                        "type": "final_webhook_status",
                        "session_id": str(session.session_id) if session else "unknown",
                        "delivery_status": final_webhook_status,
                    })
            except Exception as e:
                logger.error(f"Error sending final webhook status: {e}")
        
        if session:
            try:
                await session_manager.end_session(session.session_id)
            except Exception as e:
                logger.error(f"Error ending session: {e}")
        
        if transcriber:
            try:
                final_delivery_result = await transcriber.stop()
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
