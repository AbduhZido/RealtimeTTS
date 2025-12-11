import asyncio
import time
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from meet_transcriber.transcript_buffer import TranscriptBuffer, TranscriptSegment


class TestTranscriptBuffer:
    """Test cases for TranscriptBuffer functionality."""
    
    @pytest.fixture
    def session_id(self):
        return uuid4()
    
    @pytest.fixture
    def meeting_metadata(self):
        return {
            "title": "Test Meeting",
            "participants": ["user1@example.com"],
            "language": "en"
        }
    
    @pytest.fixture
    def buffer(self, session_id, meeting_metadata):
        return TranscriptBuffer(
            session_id=session_id,
            meeting_metadata=meeting_metadata,
            flush_interval=5.0,
            max_segments_before_flush=10
        )
    
    def test_buffer_initialization(self, buffer, session_id, meeting_metadata):
        """Test buffer initialization."""
        assert buffer.session_id == session_id
        assert buffer.meeting_metadata == meeting_metadata
        assert buffer.flush_interval == 5.0
        assert buffer.max_segments_before_flush == 10
        assert len(buffer.segments) == 0
        assert buffer._current_text_buffer == ""
        assert isinstance(buffer._start_time, float)
    
    def test_add_segment_final(self, buffer):
        """Test adding a final segment."""
        text = "Hello world"
        buffer.add_segment(text, is_final=True, speaker_id="user1", confidence=0.95)
        
        assert len(buffer.segments) == 1
        segment = buffer.segments[0]
        assert segment.text == "Hello world"
        assert segment.is_final is True
        assert segment.speaker_id == "user1"
        assert segment.confidence == 0.95
        assert buffer.get_current_transcript() == "Hello world"
    
    def test_add_segment_partial(self, buffer):
        """Test adding a partial (non-final) segment."""
        text = "Hello wor"
        buffer.add_segment(text, is_final=False)
        
        assert len(buffer.segments) == 1
        segment = buffer.segments[0]
        assert segment.text == "Hello wor"
        assert segment.is_final is False
        assert buffer.get_current_transcript() == "Hello wor"
    
    def test_add_multiple_segments(self, buffer):
        """Test adding multiple segments."""
        buffer.add_segment("Hello", is_final=True)
        buffer.add_segment("world", is_final=False)
        buffer.add_segment("!", is_final=True)
        
        assert len(buffer.segments) == 3
        assert buffer.get_current_transcript() == "Hello world !"
    
    def test_segment_timing(self, buffer):
        """Test segment timing metadata."""
        start_time = time.time()
        buffer.add_segment("Test", is_final=True)
        end_time = time.time()
        
        segment = buffer.segments[0]
        assert segment.start_time >= start_time
        assert segment.end_time >= segment.start_time
        assert segment.end_time <= end_time
    
    def test_flush_empty_buffer(self, buffer):
        """Test flushing empty buffer."""
        payload = asyncio.run(buffer.flush())
        
        assert payload["session_id"] == str(buffer.session_id)
        assert payload["meeting_metadata"] == buffer.meeting_metadata
        assert payload["transcript_segments"] == []
        assert payload["full_transcript"] == ""
        assert payload["stats"]["total_segments"] == 0
        assert payload["stats"]["final_segments"] == 0
    
    @pytest.mark.asyncio
    async def test_flush_with_segments(self, buffer):
        """Test flushing buffer with segments."""
        buffer.add_segment("Hello", is_final=True)
        buffer.add_segment("world", is_final=False)
        buffer.add_segment("!", is_final=True)
        
        payload = await buffer.flush()
        
        assert len(payload["transcript_segments"]) == 3
        assert payload["full_transcript"] == "Hello world !"
        assert payload["stats"]["total_segments"] == 3
        assert payload["stats"]["final_segments"] == 2
        assert payload["stats"]["partial_segments"] == 1
        
        # Buffer should be cleared after flush
        assert len(buffer.segments) == 0
        assert buffer.get_current_transcript() == ""
    
    @pytest.mark.asyncio
    async def test_flush_preserves_final_segments(self, buffer):
        """Test that final segments are preserved after flush."""
        buffer.add_segment("Hello", is_final=True)
        buffer.add_segment("world", is_final=False)
        buffer.add_segment("!", is_final=True)
        
        payload = await buffer.flush()
        
        # Only final segments should remain
        assert len(buffer.segments) == 2
        assert all(segment.is_final for segment in buffer.segments)
        assert buffer.get_current_transcript() == "Hello !"
    
    def test_time_based_flush_trigger(self, session_id, meeting_metadata):
        """Test that time-based flush is triggered."""
        # Use very short flush interval for testing
        buffer = TranscriptBuffer(
            session_id=session_id,
            meeting_metadata=meeting_metadata,
            flush_interval=0.1,  # 100ms
            max_segments_before_flush=100
        )
        
        # Mock the flush callback
        mock_callback = MagicMock()
        buffer.set_flush_callback(mock_callback)
        
        # Add a segment and wait for time-based flush
        buffer.add_segment("Test", is_final=False)
        
        # Wait for flush interval + small buffer
        time.sleep(0.2)
        
        # Callback should have been called
        mock_callback.assert_called()
    
    def test_count_based_flush_trigger(self, session_id, meeting_metadata):
        """Test that segment count-based flush is triggered."""
        # Use low segment count for testing
        buffer = TranscriptBuffer(
            session_id=session_id,
            meeting_metadata=meeting_metadata,
            flush_interval=60.0,  # Very long interval
            max_segments_before_flush=3
        )
        
        # Mock the flush callback
        mock_callback = MagicMock()
        buffer.set_flush_callback(mock_callback)
        
        # Add segments to trigger count-based flush
        buffer.add_segment("Hello", is_final=False)
        buffer.add_segment("world", is_final=False)
        buffer.add_segment("!", is_final=False)
        
        # Callback should have been called when count exceeded
        mock_callback.assert_called()
    
    def test_final_segments_flush_immediately(self, session_id, meeting_metadata):
        """Test that final segments trigger immediate flush."""
        buffer = TranscriptBuffer(
            session_id=session_id,
            meeting_metadata=meeting_metadata,
            flush_interval=60.0,  # Very long interval
            max_segments_before_flush=100
        )
        
        # Mock the flush callback
        mock_callback = MagicMock()
        buffer.set_flush_callback(mock_callback)
        
        # Add a final segment
        buffer.add_segment("Final text", is_final=True)
        
        # Small delay to ensure flush check
        time.sleep(0.1)
        
        # Callback should have been called for final segment
        mock_callback.assert_called()
    
    @pytest.mark.asyncio
    async def test_final_flush(self, buffer):
        """Test final flush operation."""
        buffer.add_segment("Hello", is_final=True)
        buffer.add_segment("world", is_final=False)
        
        payload = await buffer.final_flush()
        
        # All segments should be marked as final in final payload
        for segment in payload["transcript_segments"]:
            assert segment["is_final"] is True
        
        assert payload["is_final"] is True
        assert payload["full_transcript"] == "Hello world"
    
    def test_clear_buffer(self, buffer):
        """Test buffer clearing."""
        buffer.add_segment("Hello", is_final=True)
        buffer.add_segment("world", is_final=False)
        
        assert len(buffer.segments) == 2
        assert buffer.get_current_transcript() == "Hello world"
        
        buffer.clear()
        
        assert len(buffer.segments) == 0
        assert buffer.get_current_transcript() == ""
    
    def test_segment_id_uniqueness(self, buffer):
        """Test that segment IDs are unique."""
        buffer.add_segment("First", is_final=True)
        buffer.add_segment("Second", is_final=True)
        
        segment_ids = [seg.segment_id for seg in buffer.segments]
        assert len(segment_ids) == len(set(segment_ids))  # All unique
    
    def test_empty_text_handling(self, buffer):
        """Test handling of empty text segments."""
        buffer.add_segment("", is_final=True)
        buffer.add_segment("   ", is_final=True)
        buffer.add_segment("Valid text", is_final=True)
        
        # Empty/whitespace-only segments should not be added
        assert len(buffer.segments) == 1
        assert buffer.segments[0].text == "Valid text"
    
    def test_payload_structure(self, buffer):
        """Test payload structure completeness."""
        buffer.add_segment("Test", is_final=True)
        
        payload = asyncio.run(buffer.flush())
        
        required_fields = [
            "session_id", "meeting_metadata", "timestamp", 
            "transcript_segments", "full_transcript", "stats"
        ]
        
        for field in required_fields:
            assert field in payload
        
        # Check transcript segment structure
        if payload["transcript_segments"]:
            segment = payload["transcript_segments"][0]
            segment_fields = [
                "segment_id", "text", "start_time", "end_time",
                "is_final", "speaker_id", "confidence"
            ]
            for field in segment_fields:
                assert field in segment
        
        # Check stats structure
        stats_fields = [
            "total_segments", "final_segments", "partial_segments",
            "total_duration", "buffer_size_chars"
        ]
        for field in stats_fields:
            assert field in payload["stats"]