import asyncio
import logging
import numpy as np
from typing import Callable, Optional, Any

try:
    from RealtimeSTT import AudioToTextRecorder
except ImportError:
    AudioToTextRecorder = None

from .transcript_buffer import TranscriptBuffer
from .n8n_client import N8NWebhookClient

logger = logging.getLogger(__name__)


class AudioTranscriber:
    def __init__(
        self,
        model_name: str = "tiny.en",
        language: str = "en",
        on_transcript: Optional[Callable[[str, bool], None]] = None,
        transcript_buffer: Optional[TranscriptBuffer] = None,
        n8n_client: Optional[N8NWebhookClient] = None,
        meeting_metadata: Optional[dict] = None,
    ):
        self.model_name = model_name
        self.language = language
        self.on_transcript = on_transcript
        self.transcript_buffer = transcript_buffer
        self.n8n_client = n8n_client
        self.meeting_metadata = meeting_metadata or {}
        self._recorder = None
        self._is_running = False
        
    async def initialize(self):
        if AudioToTextRecorder is None:
            raise ImportError(
                "RealtimeSTT is not installed. Please install it with: pip install RealtimeSTT"
            )
        
        try:
            self._recorder = AudioToTextRecorder(
                model=self.model_name,
                language=self.language,
                spinner=False,
                silero_sensitivity=0.4,
                webrtc_sensitivity=2,
                post_speech_silence_duration=0.4,
                min_length_of_recording=0.5,
                min_gap_between_recordings=0,
                enable_realtime_transcription=True,
                realtime_processing_pause=0.1,
                realtime_model_type=self.model_name,
                on_realtime_transcription_update=self._on_realtime_update,
                on_realtime_transcription_stabilized=self._on_stabilized,
            )
            logger.info(f"Initialized transcriber with model {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize transcriber: {e}")
            raise
    
    def _on_realtime_update(self, text: str):
        if text.strip():
            try:
                # Call original callback if provided
                if self.on_transcript:
                    self.on_transcript(text, False)
                
                # Add to transcript buffer if available
                if self.transcript_buffer:
                    self.transcript_buffer.add_segment(text, False)
                    
            except Exception as e:
                logger.error(f"Error in transcript callback: {e}")
    
    def _on_stabilized(self, text: str):
        if text.strip():
            try:
                # Call original callback if provided
                if self.on_transcript:
                    self.on_transcript(text, True)
                
                # Add to transcript buffer if available
                if self.transcript_buffer:
                    self.transcript_buffer.add_segment(text, True)
                    
            except Exception as e:
                logger.error(f"Error in transcript callback: {e}")
    
    async def process_audio_queue(self, audio_queue: asyncio.Queue):
        if not self._recorder:
            await self.initialize()
        
        self._is_running = True
        logger.info("Starting audio processing")
        
        try:
            while self._is_running:
                try:
                    audio_data = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
                    
                    if audio_data is None:
                        logger.info("Received stop signal")
                        break
                    
                    if isinstance(audio_data, bytes):
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)
                        audio_float = audio_array.astype(np.float32) / 32768.0
                        
                        if self._recorder:
                            await asyncio.to_thread(
                                self._recorder.feed_audio, audio_float
                            )
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing audio: {e}")
                    
        except Exception as e:
            logger.error(f"Fatal error in audio processing: {e}")
        finally:
            self._is_running = False
            logger.info("Stopped audio processing")
    
    async def _send_webhook_if_enabled(self, payload: dict, is_final: bool = False):
        """Send webhook payload if N8N client is configured."""
        if self.n8n_client and payload:
            try:
                session_id = str(self.transcript_buffer.session_id) if self.transcript_buffer else "unknown"
                
                if is_final:
                    delivery_result = await self.n8n_client.send_final_transcript(payload, session_id)
                else:
                    delivery_result = await self.n8n_client.send_transcript(payload, session_id)
                
                # Log delivery status
                if delivery_result["success"]:
                    logger.info(f"Webhook delivered successfully (session: {session_id})")
                else:
                    logger.error(f"Webhook delivery failed (session: {session_id}): {delivery_result.get('last_error', 'Unknown error')}")
                
                return delivery_result
                
            except Exception as e:
                logger.error(f"Error sending webhook: {e}")
                return {"success": False, "error": str(e)}
        
        return None
    
    async def stop(self, deliver_final_webhook: bool = True):
        """Stop the transcriber and optionally deliver final transcript to webhook."""
        self._is_running = False
        
        # Perform final webhook delivery if requested and enabled
        final_delivery_result = None
        if deliver_final_webhook and self.transcript_buffer and self.n8n_client:
            try:
                final_payload = await self.transcript_buffer.final_flush()
                final_delivery_result = await self._send_webhook_if_enabled(final_payload, is_final=True)
            except Exception as e:
                logger.error(f"Error delivering final transcript to webhook: {e}")
        
        if self._recorder:
            try:
                await asyncio.to_thread(self._recorder.shutdown)
            except Exception as e:
                logger.error(f"Error shutting down recorder: {e}")
        
        return final_delivery_result
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
