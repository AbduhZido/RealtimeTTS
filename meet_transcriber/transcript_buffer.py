import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """Represents a single transcript segment with timing information."""
    text: str
    is_final: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "is_final": self.is_final,
            "timestamp": self.timestamp.isoformat(),
        }


class TranscriptBuffer:
    """
    Aggregates transcript segments and provides methods to query and reset buffer state.
    """
    
    def __init__(self):
        self.segments: List[TranscriptSegment] = []
        self.created_at = datetime.utcnow()
    
    def add_segment(self, text: str, is_final: bool) -> None:
        """Add a new transcript segment to the buffer."""
        segment = TranscriptSegment(text=text, is_final=is_final)
        self.segments.append(segment)
        logger.debug(
            f"Added segment: '{text}' (final={is_final}), total segments: {len(self.segments)}"
        )
    
    def get_full_transcript(self) -> str:
        """Get the concatenated transcript from all segments."""
        return " ".join(segment.text for segment in self.segments).strip()
    
    def get_final_segments(self) -> List[Dict[str, Any]]:
        """Get only the final segments."""
        return [s.to_dict() for s in self.segments if s.is_final]
    
    def get_all_segments(self) -> List[Dict[str, Any]]:
        """Get all segments including interim ones."""
        return [s.to_dict() for s in self.segments]
    
    def has_final_segments(self) -> bool:
        """Check if buffer has any finalized segments."""
        return any(segment.is_final for segment in self.segments)
    
    def should_flush(self) -> bool:
        """Determine if buffer should be flushed (has final segments)."""
        return self.has_final_segments()
    
    def reset(self) -> None:
        """Clear the buffer and reset timestamp."""
        self.segments.clear()
        self.created_at = datetime.utcnow()
        logger.debug("Transcript buffer reset")
    
    def get_buffer_info(self) -> Dict[str, Any]:
        """Get information about the current buffer state."""
        return {
            "segment_count": len(self.segments),
            "final_count": sum(1 for s in self.segments if s.is_final),
            "created_at": self.created_at.isoformat(),
        }
