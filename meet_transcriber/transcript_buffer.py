import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """Represents a segment of transcript text with metadata."""
    text: str
    start_time: float
    end_time: float
    is_final: bool
    segment_id: str
    speaker_id: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class TranscriptBuffer:
    """Buffers transcript segments and aggregates full transcript."""
    
    session_id: UUID
    meeting_metadata: Dict[str, Any]
    flush_interval: float = 10.0  # seconds
    max_segments_before_flush: int = 50
    
    def __post_init__(self):
        self.segments: List[TranscriptSegment] = []
        self._start_time = time.time()
        self._flush_callback: Optional[Callable[[], None]] = None
        self._flush_task: Optional[asyncio.Task] = None
        self._current_text_buffer = ""
        self._last_flush_time = time.time()
    
    def add_segment(
        self, 
        text: str, 
        is_final: bool, 
        speaker_id: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> None:
        """Add a transcript segment to the buffer."""
        # Skip empty or whitespace-only text
        if not text or not text.strip():
            return
            
        now = time.time()
        end_time = now
        
        # Calculate start time (end_time minus estimated duration)
        # For simplicity, estimate based on text length (rough approximation)
        estimated_duration = max(0.1, len(text) * 0.1)  # ~0.1s per character
        start_time = end_time - estimated_duration
        
        segment = TranscriptSegment(
            text=text.strip(),
            start_time=start_time,
            end_time=end_time,
            is_final=is_final,
            segment_id=f"{self.session_id}_{len(self.segments)}",
            speaker_id=speaker_id,
            confidence=confidence,
        )
        
        self.segments.append(segment)
        self._current_text_buffer += " " + segment.text if self._current_text_buffer else segment.text
        self._current_text_buffer = self._current_text_buffer.strip()
        
        logger.debug(f"Added segment: '{segment.text}' (final: {is_final}, total segments: {len(self.segments)})")
        
        # Check if we should flush
        self._check_flush_conditions()
    
    def _check_flush_conditions(self) -> None:
        """Check if buffer should be flushed based on conditions."""
        should_flush = False
        
        # Time-based flush
        time_since_flush = time.time() - self._last_flush_time
        if time_since_flush >= self.flush_interval:
            should_flush = True
            logger.debug(f"Time-based flush triggered (interval: {self.flush_interval}s)")
        
        # Segment count-based flush
        if len(self.segments) >= self.max_segments_before_flush:
            should_flush = True
            logger.debug(f"Segment count flush triggered (count: {len(self.segments)})")
        
        # Always flush if we have final segments
        final_segments = [s for s in self.segments if s.is_final]
        if final_segments and time_since_flush >= 2.0:  # Minimum 2s between flushes for final segments
            should_flush = True
            logger.debug(f"Final segment flush triggered")
        
        if should_flush and self._flush_callback:
            asyncio.create_task(self.flush())
    
    async def flush(self) -> Dict[str, Any]:
        """Flush the buffer and return the transcript payload."""
        if not self.segments:
            return self._create_payload("")
        
        # Create the full transcript by concatenating all segments
        full_transcript = " ".join([segment.text for segment in self.segments if segment.text])
        
        payload = self._create_payload(full_transcript)
        
        # Clear the buffer but keep final segments for context
        # Remove only non-final segments that have been successfully sent
        final_segments = [s for s in self.segments if s.is_final]
        
        self.segments = final_segments
        self._current_text_buffer = " ".join([s.text for s in final_segments if s.text])
        self._last_flush_time = time.time()
        
        logger.debug(f"Flushed buffer with {len(payload['transcript_segments'])} segments, full transcript length: {len(full_transcript)}")
        
        return payload
    
    def _create_payload(self, full_transcript: str) -> Dict[str, Any]:
        """Create the N8N webhook payload."""
        return {
            "session_id": str(self.session_id),
            "meeting_metadata": self.meeting_metadata,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "transcript_segments": [
                {
                    "segment_id": seg.segment_id,
                    "text": seg.text,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "is_final": seg.is_final,
                    "speaker_id": seg.speaker_id,
                    "confidence": seg.confidence,
                }
                for seg in self.segments
            ],
            "full_transcript": full_transcript,
            "stats": {
                "total_segments": len(self.segments),
                "final_segments": len([s for s in self.segments if s.is_final]),
                "partial_segments": len([s for s in self.segments if not s.is_final]),
                "total_duration": self.segments[-1].end_time - self.segments[0].start_time if self.segments else 0,
                "buffer_size_chars": len(full_transcript),
            }
        }
    
    def get_current_transcript(self) -> str:
        """Get the current accumulated transcript without flushing."""
        return self._current_text_buffer.strip()
    
    def set_flush_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when buffer is flushed."""
        self._flush_callback = callback
    
    async def final_flush(self) -> Dict[str, Any]:
        """Perform a final flush with all remaining segments."""
        logger.info(f"Performing final flush for session {self.session_id}")
        payload = await self.flush()
        
        # Ensure all segments are marked as final in the final payload
        for segment in payload["transcript_segments"]:
            segment["is_final"] = True
        
        payload["full_transcript"] = " ".join([seg.text for seg in self.segments if seg.text])
        payload["is_final"] = True
        
        return payload
    
    def clear(self) -> None:
        """Clear the buffer entirely."""
        self.segments.clear()
        self._current_text_buffer = ""
        self._last_flush_time = time.time()
        logger.debug(f"Cleared transcript buffer for session {self.session_id}")