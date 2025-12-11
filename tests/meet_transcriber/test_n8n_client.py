import asyncio
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError
import aiohttp

from meet_transcriber.n8n_client import N8NWebhookClient, N8NWebhookError


class TestN8NWebhookClient:
    """Test cases for N8NWebhookClient functionality."""
    
    @pytest.fixture
    def webhook_url(self):
        return "https://webhook.example.com/transcript"
    
    @pytest.fixture
    def client(self, webhook_url):
        return N8NWebhookClient(
            webhook_url=webhook_url,
            max_retries=2,
            retry_delay=0.1,
            backoff_factor=2.0,
            timeout=5.0,
            headers={"Authorization": "Bearer test-token"}
        )
    
    def test_client_initialization(self, client, webhook_url):
        """Test client initialization."""
        assert client.webhook_url == webhook_url
        assert client.max_retries == 2
        assert client.retry_delay == 0.1
        assert client.backoff_factor == 2.0
        assert client.timeout == 5.0
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-token"
        assert "Content-Type" in client.headers
        assert client.headers["Content-Type"] == "application/json"
        assert "User-Agent" in client.headers
        assert client.headers["User-Agent"] == "MeetTranscriber/1.0"
    
    def test_invalid_webhook_url(self):
        """Test error handling for invalid webhook URL."""
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            N8NWebhookClient("invalid-url")
        
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            N8NWebhookClient("ftp://example.com")
        
        with pytest.raises(ValueError, match="Invalid webhook URL"):
            N8NWebhookClient("http://")
    
    @pytest.mark.asyncio
    async def test_successful_delivery(self, client):
        """Test successful webhook delivery."""
        payload = {
            "session_id": "test-session",
            "transcript": "Hello world",
            "is_final": True
        }
        
        # Mock successful HTTP response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "success"})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.send_transcript(payload, "test-session")
            
            # Verify result
            assert result["success"] is True
            assert result["final_status"] == "delivered"
            assert result["attempts"][0]["success"] is True
            assert result["attempts"][0]["status_code"] == 200
            assert "n8n_response" in result
            
            # Verify HTTP call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check payload was sent
            sent_payload = call_args[1]["json"]
            assert sent_payload == payload
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, client):
        """Test retry logic on webhook failure."""
        payload = {"test": "data"}
        
        # Mock failed responses for first two attempts, success on third
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_responses = [
                # First attempt: 500 error
                AsyncMock(status=500, text=AsyncMock(return_value="Internal Server Error")),
                # Second attempt: network error
                AsyncMock(status=503, text=AsyncMock(return_value="Service Unavailable")),
                # Third attempt: success
                AsyncMock(status=200, json=AsyncMock(return_value={"success": True}))
            ]
            
            mock_post.return_value.__aenter__.side_effect = mock_responses
            
            result = await client.send_transcript(payload, "test-session")
            
            # Should have attempted 3 times (1 initial + 2 retries)
            assert len(result["attempts"]) == 3
            assert result["success"] is True
            assert result["final_status"] == "delivered"
            
            # Verify retries occurred
            assert not result["attempts"][0]["success"]
            assert not result["attempts"][1]["success"]
            assert result["attempts"][2]["success"]
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client):
        """Test behavior when max retries are exceeded."""
        payload = {"test": "data"}
        
        # Mock all attempts failing
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.send_transcript(payload, "test-session")
            
            # Should have attempted 3 times (max_retries + 1)
            assert len(result["attempts"]) == 3
            assert result["success"] is False
            assert result["final_status"] == "failed"
            assert "last_error" in result
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Test timeout handling."""
        payload = {"test": "data"}
        
        # Mock timeout exception
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")
            
            result = await client.send_transcript(payload, "test-session")
            
            assert result["success"] is False
            assert result["final_status"] == "failed"
            assert any("timeout" in attempt.get("error", "").lower() 
                      for attempt in result["attempts"])
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, client):
        """Test network error handling."""
        payload = {"test": "data"}
        
        # Mock network error
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = ClientError("Connection failed")
            
            result = await client.send_transcript(payload, "test-session")
            
            assert result["success"] is False
            assert result["final_status"] == "failed"
            assert any("client error" in attempt.get("error", "").lower() 
                      for attempt in result["attempts"])
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, client):
        """Test exponential backoff timing."""
        payload = {"test": "data"}
        
        # Mock all attempts failing
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_post.return_value.__aenter__.return_value = mock_response
            
            start_time = time.time()
            await client.send_transcript(payload, "test-session")
            end_time = time.time()
            
            # Should wait: 0.1s + 0.2s = 0.3s total
            # Add some tolerance for test execution time
            assert end_time - start_time >= 0.25
    
    @pytest.mark.asyncio
    async def test_final_transcript_delivery(self, client):
        """Test final transcript delivery."""
        payload = {"transcript": "Final transcript", "is_final": True}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.send_final_transcript(payload, "test-session")
            
            assert result["success"] is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delivery_history_tracking(self, client):
        """Test delivery history tracking."""
        payload = {"test": "data"}
        
        # First delivery attempt
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await client.send_transcript(payload, "session1")
            await client.send_transcript(payload, "session2")
            
            # Check history
            assert client.total_deliveries == 2
            assert client.successful_deliveries == 2
            assert client.failed_deliveries == 0
            
            # Check recent deliveries
            recent = client.get_recent_deliveries(1)
            assert len(recent) == 1
            assert recent[0]["session_id"] == "session2"
    
    @pytest.mark.asyncio
    async def test_delivery_status_lookup(self, client):
        """Test delivery status lookup by session."""
        payload = {"test": "data"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await client.send_transcript(payload, "session1")
            await client.send_transcript(payload, "session2")
            
            # Get status for session1
            status = client.get_delivery_status("session1")
            assert status is not None
            assert status["session_id"] == "session1"
            assert status["success"] is True
            
            # Get status for non-existent session
            status = client.get_delivery_status("nonexistent")
            assert status is None
    
    def test_clear_history(self, client):
        """Test clearing delivery history."""
        # Add some mock history entries
        client._delivery_history = [
            {"session_id": "test1", "success": True},
            {"session_id": "test2", "success": False}
        ]
        
        assert client.total_deliveries == 2
        
        client.clear_history()
        
        assert client.total_deliveries == 0
        assert client.successful_deliveries == 0
        assert client.failed_deliveries == 0
    
    @pytest.mark.asyncio
    async def test_non_json_response_handling(self, client):
        """Test handling of non-JSON responses from N8N."""
        payload = {"test": "data"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.text = AsyncMock(return_value="Plain text response")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.send_transcript(payload, "test-session")
            
            assert result["success"] is True
            assert "n8n_response" in result
            assert "raw_response" in result["n8n_response"]
            assert result["n8n_response"]["raw_response"] == "Plain text response"
    
    @pytest.mark.asyncio
    async def test_custom_headers_preserved(self, client):
        """Test that custom headers are preserved in requests."""
        payload = {"test": "data"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await client.send_transcript(payload, "test-session")
            
            # Check headers were passed
            call_args = mock_post.call_args
            sent_headers = call_args[1]["headers"]
            
            assert sent_headers["Authorization"] == "Bearer test-token"
            assert sent_headers["Content-Type"] == "application/json"
            assert sent_headers["User-Agent"] == "MeetTranscriber/1.0"
    
    @pytest.mark.asyncio
    async def test_empty_payload(self, client):
        """Test handling of empty payload."""
        payload = {}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await client.send_transcript(payload, "test-session")
            
            assert result["success"] is True
            assert result["payload_size"] == 2  # "{}"
            
            # Check payload was sent
            call_args = mock_post.call_args
            sent_payload = call_args[1]["json"]
            assert sent_payload == {}
    
    def test_delivery_metrics(self, client):
        """Test delivery metrics calculation."""
        # Mock some history
        client._delivery_history = [
            {"success": True},
            {"success": True},
            {"success": False},
            {"success": False},
            {"success": False}
        ]
        
        assert client.total_deliveries == 5
        assert client.successful_deliveries == 2
        assert client.failed_deliveries == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_deliveries(self, client):
        """Test concurrent webhook deliveries."""
        payload = {"test": "data"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Send multiple concurrent requests
            tasks = [
                client.send_transcript(payload, f"session{i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(result["success"] for result in results)
            assert client.total_deliveries == 5