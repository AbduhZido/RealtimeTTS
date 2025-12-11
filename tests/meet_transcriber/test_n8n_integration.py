import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from meet_transcriber.n8n_client import N8NWebhookClient
from meet_transcriber.transcript_buffer import TranscriptBuffer


@pytest.mark.asyncio
async def test_webhook_integration_with_transcript_buffer():
    """Integration test: Transcript buffer → N8N webhook."""
    
    client = N8NWebhookClient(
        webhook_url="https://n8n.example.com/webhook/transcript",
        max_retries=1,
        retry_delay=0.1,
    )
    
    buffer = TranscriptBuffer()
    buffer.add_segment("Hello everyone", is_final=False)
    buffer.add_segment("welcome to the meeting", is_final=True)
    buffer.add_segment("Let's begin", is_final=True)
    
    payload = {
        "meeting_metadata": {
            "session_id": "test-session-123",
            "participants": [
                {"name": "Alice", "role": "speaker"},
                {"name": "Bob", "role": "participant"},
            ],
            "meeting_id": "meeting-001",
            "meeting_title": "Team Sync",
            "language": "en",
            "start_time": buffer.created_at.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
        },
        "transcript": {
            "full": buffer.get_full_transcript(),
            "segments": buffer.get_all_segments(),
        },
        "delivery_status": "pending",
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.send_payload(payload)
    
    assert result is True
    assert payload["transcript"]["full"] == "Hello everyone welcome to the meeting Let's begin"
    assert len(payload["transcript"]["segments"]) == 3
    assert payload["meeting_metadata"]["participants"][0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_transcript_buffer_segment_ordering():
    """Test that segments maintain chronological order."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("First", is_final=False)
    await asyncio.sleep(0.01)
    buffer.add_segment("Second", is_final=True)
    await asyncio.sleep(0.01)
    buffer.add_segment("Third", is_final=False)
    
    segments = buffer.get_all_segments()
    
    assert len(segments) == 3
    assert segments[0]["text"] == "First"
    assert segments[1]["text"] == "Second"
    assert segments[2]["text"] == "Third"
    
    assert segments[0]["timestamp"] < segments[1]["timestamp"]
    assert segments[1]["timestamp"] < segments[2]["timestamp"]


@pytest.mark.asyncio
async def test_buffer_final_segments_only():
    """Test filtering for final segments only."""
    buffer = TranscriptBuffer()
    
    buffer.add_segment("Interim one", is_final=False)
    buffer.add_segment("Interim two", is_final=False)
    buffer.add_segment("Final one", is_final=True)
    buffer.add_segment("Interim three", is_final=False)
    buffer.add_segment("Final two", is_final=True)
    
    final_segments = buffer.get_final_segments()
    
    assert len(final_segments) == 2
    assert final_segments[0]["text"] == "Final one"
    assert final_segments[1]["text"] == "Final two"
    
    all_segments = buffer.get_all_segments()
    assert len(all_segments) == 5


@pytest.mark.asyncio
async def test_webhook_with_empty_transcript():
    """Test handling empty transcript."""
    client = N8NWebhookClient(webhook_url="https://n8n.example.com/webhook")
    buffer = TranscriptBuffer()
    
    payload = {
        "meeting_metadata": {
            "session_id": "empty-session",
        },
        "transcript": {
            "full": buffer.get_full_transcript(),
            "segments": buffer.get_all_segments(),
        },
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.send_payload(payload)
    
    assert result is True
    assert payload["transcript"]["full"] == ""
    assert len(payload["transcript"]["segments"]) == 0
