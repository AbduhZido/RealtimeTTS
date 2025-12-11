from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MEET_TRANSCRIBER_",
        case_sensitive=False,
    )
    
    model_name: str = "tiny.en"
    language: str = "en"
    auth_token: Optional[str] = None
    max_concurrent_sessions: int = 10
    host: str = "0.0.0.0"
    port: int = 8765
    log_level: str = "INFO"
    n8n_webhook_url: Optional[str] = None
    n8n_max_retries: int = 3
    n8n_retry_delay: float = 1.0
    n8n_timeout: float = 30.0


settings = Settings()
