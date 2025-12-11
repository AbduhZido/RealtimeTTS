import asyncio
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from meet_transcriber.n8n_client import N8NWebhookClient


@pytest.mark.asyncio
async def test_send_payload_success(monkeypatch):
    """Test successful webhook delivery."""
    client = N8NWebhookClient(
        webhook_url="https://example.com/webhook",
        max_retries=3,
        retry_delay=1.0,
    )
    
    payload = {
        "meeting_id": "test-123",
        "transcript": "Hello world",
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
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://example.com/webhook"
    assert call_args[1]["json"] == payload


@pytest.mark.asyncio
async def test_send_payload_no_webhook_url():
    """Test when webhook URL is not configured."""
    client = N8NWebhookClient(webhook_url="")
    
    payload = {"transcript": "test"}
    result = await client.send_payload(payload)
    
    assert result is False


@pytest.mark.asyncio
async def test_send_payload_http_error(monkeypatch):
    """Test handling of HTTP errors."""
    client = N8NWebhookClient(
        webhook_url="https://example.com/webhook",
        max_retries=1,
        retry_delay=0.1,
    )
    
    payload = {"transcript": "test"}
    
    error_response = MagicMock()
    error_response.status_code = 500
    error_response.text = "Internal Server Error"
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error",
        request=MagicMock(),
        response=error_response,
    )
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = error_response
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.send_payload(payload)
    
    assert result is False
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_send_payload_connection_error(monkeypatch):
    """Test handling of connection errors."""
    client = N8NWebhookClient(
        webhook_url="https://example.com/webhook",
        max_retries=1,
        retry_delay=0.1,
    )
    
    payload = {"transcript": "test"}
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = httpx.ConnectError("Connection failed")
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.send_payload(payload)
    
    assert result is False
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_send_payload_timeout_error(monkeypatch):
    """Test handling of timeout errors."""
    client = N8NWebhookClient(
        webhook_url="https://example.com/webhook",
        max_retries=1,
        retry_delay=0.1,
    )
    
    payload = {"transcript": "test"}
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = httpx.TimeoutException("Timeout")
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.send_payload(payload)
    
    assert result is False
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_send_payload_retry_succeeds_on_second_attempt(monkeypatch):
    """Test successful retry after initial failure."""
    client = N8NWebhookClient(
        webhook_url="https://example.com/webhook",
        max_retries=2,
        retry_delay=0.1,
    )
    
    payload = {"transcript": "test"}
    
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    mock_client.post.side_effect = [
        httpx.ConnectError("Connection failed"),
        success_response,
    ]
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await client.send_payload(payload)
    
    assert result is True
    assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_send_payload_exponential_backoff(monkeypatch):
    """Test exponential backoff between retries."""
    client = N8NWebhookClient(
        webhook_url="https://example.com/webhook",
        max_retries=2,
        retry_delay=0.1,
    )
    
    payload = {"transcript": "test"}
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.side_effect = httpx.TimeoutException("Timeout")
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await client.send_payload(payload)
    
    assert result is False
    assert mock_sleep.call_count == 2
    
    sleep_calls = mock_sleep.call_args_list
    assert sleep_calls[0][0][0] == 0.1
    assert sleep_calls[1][0][0] == 0.2
