import pytest
from datetime import datetime

from meet_transcriber.transcript_buffer import TranscriptBuffer, TranscriptSegment


def test_transcript_segment_to_dict():
    """Test TranscriptSegment serialization."""
    segment = TranscriptSegment(text="Hello world", is_final=True)
    
    data = segment.to_dict()
    assert data["text"] == "Hello world"
    assert data["is_final"] is True
    assert "timestamp" in data


def test_buffer_add_segment():
    """Test adding segments to buffer."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=False)
    buffer.add_segment("world", is_final=True)
    
    assert len(buffer.segments) == 2
    assert buffer.segments[0].text == "Hello"
    assert buffer.segments[1].text == "world"


def test_buffer_get_full_transcript():
    """Test concatenating full transcript."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=False)
    buffer.add_segment("world", is_final=True)
    buffer.add_segment("test", is_final=False)
    
    full = buffer.get_full_transcript()
    assert full == "Hello world test"


def test_buffer_get_final_segments():
    """Test getting only final segments."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=False)
    buffer.add_segment("world", is_final=True)
    buffer.add_segment("test", is_final=False)
    buffer.add_segment("final", is_final=True)
    
    final_segments = buffer.get_final_segments()
    assert len(final_segments) == 2
    assert final_segments[0]["text"] == "world"
    assert final_segments[1]["text"] == "final"


def test_buffer_get_all_segments():
    """Test getting all segments."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=False)
    buffer.add_segment("world", is_final=True)
    
    all_segments = buffer.get_all_segments()
    assert len(all_segments) == 2


def test_buffer_has_final_segments():
    """Test checking for final segments."""
    buffer = TranscriptBuffer()
    
    assert not buffer.has_final_segments()
    
    buffer.add_segment("Hello", is_final=False)
    assert not buffer.has_final_segments()
    
    buffer.add_segment("world", is_final=True)
    assert buffer.has_final_segments()


def test_buffer_should_flush():
    """Test flush condition."""
    buffer = TranscriptBuffer()
    
    assert not buffer.should_flush()
    
    buffer.add_segment("Hello", is_final=True)
    assert buffer.should_flush()


def test_buffer_reset():
    """Test buffer reset."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=True)
    buffer.add_segment("world", is_final=True)
    
    assert len(buffer.segments) == 2
    
    old_created_at = buffer.created_at
    buffer.reset()
    
    assert len(buffer.segments) == 0
    assert buffer.created_at > old_created_at


def test_buffer_get_buffer_info():
    """Test getting buffer metadata."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=False)
    buffer.add_segment("world", is_final=True)
    buffer.add_segment("test", is_final=False)
    
    info = buffer.get_buffer_info()
    
    assert info["segment_count"] == 3
    assert info["final_count"] == 1
    assert "created_at" in info


def test_buffer_empty_transcript():
    """Test full transcript from empty buffer."""
    buffer = TranscriptBuffer()
    
    full = buffer.get_full_transcript()
    assert full == ""


def test_buffer_whitespace_handling():
    """Test handling of whitespace in concatenation."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Hello", is_final=False)
    buffer.add_segment("world", is_final=True)
    
    full = buffer.get_full_transcript()
    assert full == "Hello world"
