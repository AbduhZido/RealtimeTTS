import asyncio
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class N8NWebhookClient:
    def __init__(
        self,
        webhook_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        self.webhook_url = webhook_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    async def send_payload(
        self,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Send transcript payload to N8N webhook with retry logic.
        Returns True if successful, False otherwise.
        """
        if not self.webhook_url:
            logger.warning("N8N webhook URL not configured")
            return False

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload,
                    )
                    response.raise_for_status()
                    logger.info(
                        f"Successfully sent transcript to N8N webhook "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    return True

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error sending to N8N webhook (attempt {attempt + 1}): "
                    f"status={e.response.status_code}, body={e.response.text}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except httpx.ConnectError as e:
                logger.error(
                    f"Connection error sending to N8N webhook (attempt {attempt + 1}): {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except httpx.TimeoutException as e:
                logger.error(
                    f"Timeout sending to N8N webhook (attempt {attempt + 1}): {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except Exception as e:
                logger.error(
                    f"Unexpected error sending to N8N webhook (attempt {attempt + 1}): {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

        logger.error(
            f"Failed to send transcript to N8N webhook after {self.max_retries + 1} attempts"
        )
        return False
