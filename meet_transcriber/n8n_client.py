import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import aiohttp

logger = logging.getLogger(__name__)


class N8NWebhookError(Exception):
    """Exception raised when N8N webhook delivery fails."""
    pass


class N8NWebhookClient:
    """Client for sending transcript data to N8N webhooks with retry logic."""
    
    def __init__(
        self,
        webhook_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize N8N webhook client.
        
        Args:
            webhook_url: The N8N webhook URL to send data to
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            timeout: Request timeout in seconds
            headers: Additional headers to include in requests
        """
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.headers = headers or {}
        
        # Validate webhook URL
        parsed_url = urlparse(webhook_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid webhook URL: {webhook_url}")
        
        # Set default headers
        self.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "MeetTranscriber/1.0",
        })
        
        self._delivery_history: List[Dict[str, Any]] = []
    
    async def send_transcript(
        self, 
        payload: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Send transcript payload to N8N webhook with retry logic.
        
        Args:
            payload: The transcript payload to send
            session_id: Session identifier for logging
            
        Returns:
            Dict with delivery status and metadata
        """
        delivery_record = {
            "session_id": session_id,
            "webhook_url": self.webhook_url,
            "payload_size": len(json.dumps(payload)),
            "timestamp": time.time(),
            "attempts": [],
            "success": False,
            "final_status": None,
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            attempt_info = {
                "attempt_number": attempt + 1,
                "timestamp": time.time(),
                "success": False,
                "status_code": None,
                "error": None,
                "response_time": None,
            }
            
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.post(
                        self.webhook_url,
                        json=payload,
                        headers=self.headers,
                    ) as response:
                        attempt_info["status_code"] = response.status
                        attempt_info["response_time"] = time.time() - start_time
                        
                        if response.status == 200:
                            attempt_info["success"] = True
                            delivery_record["success"] = True
                            delivery_record["final_status"] = "delivered"
                            
                            try:
                                response_data = await response.json()
                                delivery_record["n8n_response"] = response_data
                                logger.info(
                                    f"Successfully delivered transcript to N8N webhook "
                                    f"(session: {session_id}, attempt: {attempt + 1}, "
                                    f"status: {response.status})"
                                )
                            except json.JSONDecodeError:
                                response_text = await response.text()
                                logger.warning(
                                    f"N8N webhook returned non-JSON response (session: {session_id}): {response_text[:200]}"
                                )
                                delivery_record["n8n_response"] = {"raw_response": response_text}
                            
                            break
                        else:
                            error_text = await response.text()
                            raise N8NWebhookError(
                                f"N8N webhook returned status {response.status}: {error_text}"
                            )
                            
            except asyncio.TimeoutError:
                error_msg = f"Timeout after {self.timeout}s"
                attempt_info["error"] = error_msg
                last_exception = N8NWebhookError(error_msg)
                logger.warning(
                    f"N8N webhook timeout (session: {session_id}, attempt: {attempt + 1}/{self.max_retries + 1})"
                )
                
            except aiohttp.ClientError as e:
                error_msg = f"Client error: {str(e)}"
                attempt_info["error"] = error_msg
                last_exception = N8NWebhookError(error_msg)
                logger.warning(
                    f"N8N webhook client error (session: {session_id}, attempt: {attempt + 1}/{self.max_retries + 1}): {e}"
                )
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                attempt_info["error"] = error_msg
                last_exception = N8NWebhookError(error_msg)
                logger.error(
                    f"N8N webhook unexpected error (session: {session_id}, attempt: {attempt + 1}): {e}",
                    exc_info=True
                )
            
            delivery_record["attempts"].append(attempt_info)
            
            # If this wasn't the last attempt, wait with exponential backoff
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (self.backoff_factor ** attempt)
                logger.info(
                    f"Retrying N8N webhook delivery in {wait_time:.1f}s "
                    f"(session: {session_id}, attempt: {attempt + 2}/{self.max_retries + 1})"
                )
                await asyncio.sleep(wait_time)
        
        # If we get here, all attempts failed
        if not delivery_record["success"]:
            delivery_record["final_status"] = "failed"
            delivery_record["last_error"] = str(last_exception) if last_exception else "Unknown error"
            
            logger.error(
                f"Failed to deliver transcript to N8N webhook after {self.max_retries + 1} attempts "
                f"(session: {session_id}): {last_exception}"
            )
        
        self._delivery_history.append(delivery_record)
        return delivery_record
    
    async def send_final_transcript(
        self, 
        payload: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """Send final transcript with special handling."""
        logger.info(f"Sending final transcript for session {session_id}")
        return await self.send_transcript(payload, session_id)
    
    def get_delivery_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status for a specific session."""
        for record in reversed(self._delivery_history):
            if record["session_id"] == session_id:
                return record
        return None
    
    def get_recent_deliveries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent delivery attempts."""
        return self._delivery_history[-limit:] if self._delivery_history else []
    
    def clear_history(self) -> None:
        """Clear delivery history."""
        self._delivery_history.clear()
        logger.debug("Cleared N8N webhook delivery history")
    
    @property
    def total_deliveries(self) -> int:
        """Get total number of delivery attempts."""
        return len(self._delivery_history)
    
    @property
    def successful_deliveries(self) -> int:
        """Get number of successful deliveries."""
        return len([r for r in self._delivery_history if r["success"]])
    
    @property
    def failed_deliveries(self) -> int:
        """Get number of failed deliveries."""
        return len([r for r in self._delivery_history if not r["success"]])