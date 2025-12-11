import os
import pytest
from meet_transcriber.config import Settings


def test_default_settings():
    settings = Settings()
    
    assert settings.model_name == "tiny.en"
    assert settings.language == "en"
    assert settings.auth_token is None
    assert settings.max_concurrent_sessions == 10
    assert settings.host == "0.0.0.0"
    assert settings.port == 8765
    assert settings.log_level == "INFO"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("MEET_TRANSCRIBER_MODEL_NAME", "base.en")
    monkeypatch.setenv("MEET_TRANSCRIBER_LANGUAGE", "es")
    monkeypatch.setenv("MEET_TRANSCRIBER_AUTH_TOKEN", "secret123")
    monkeypatch.setenv("MEET_TRANSCRIBER_MAX_CONCURRENT_SESSIONS", "20")
    monkeypatch.setenv("MEET_TRANSCRIBER_PORT", "9000")
    monkeypatch.setenv("MEET_TRANSCRIBER_LOG_LEVEL", "DEBUG")
    
    settings = Settings()
    
    assert settings.model_name == "base.en"
    assert settings.language == "es"
    assert settings.auth_token == "secret123"
    assert settings.max_concurrent_sessions == 20
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"


def test_default_n8n_settings():
    settings = Settings()
    
    assert settings.n8n_webhook_url is None
    assert settings.n8n_max_retries == 3
    assert settings.n8n_retry_delay == 1.0
    assert settings.n8n_timeout == 30.0


def test_n8n_settings_from_env(monkeypatch):
    monkeypatch.setenv("MEET_TRANSCRIBER_N8N_WEBHOOK_URL", "https://n8n.example.com/webhook")
    monkeypatch.setenv("MEET_TRANSCRIBER_N8N_MAX_RETRIES", "5")
    monkeypatch.setenv("MEET_TRANSCRIBER_N8N_RETRY_DELAY", "2.5")
    monkeypatch.setenv("MEET_TRANSCRIBER_N8N_TIMEOUT", "45.0")
    
    settings = Settings()
    
    assert settings.n8n_webhook_url == "https://n8n.example.com/webhook"
    assert settings.n8n_max_retries == 5
    assert settings.n8n_retry_delay == 2.5
    assert settings.n8n_timeout == 45.0
