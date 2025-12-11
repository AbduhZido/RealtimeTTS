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


settings = Settings()
