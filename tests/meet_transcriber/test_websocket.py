import json
import pytest

from meet_transcriber.config import settings


def test_settings_configuration():
    assert settings.model_name is not None
    assert settings.language is not None
    assert settings.max_concurrent_sessions > 0


def test_websocket_message_structure():
    init_message = {
        "type": "init",
        "auth_token": None,
        "participant_info": {"user": "test"}
    }
    
    assert init_message["type"] == "init"
    assert "participant_info" in init_message


def test_ready_message_structure():
    ready_message = {
        "type": "ready",
        "session_id": "test-session-id",
        "model": "tiny.en",
        "language": "en"
    }
    
    assert ready_message["type"] == "ready"
    assert "session_id" in ready_message
    assert "model" in ready_message
    assert "language" in ready_message


def test_transcript_message_structure():
    transcript_message = {
        "type": "transcript",
        "text": "Hello world",
        "is_final": True,
        "session_id": "test-session-id"
    }
    
    assert transcript_message["type"] == "transcript"
    assert "text" in transcript_message
    assert "is_final" in transcript_message
    assert "session_id" in transcript_message


def test_error_message_structure():
    error_message = {
        "type": "error",
        "message": "Test error"
    }
    
    assert error_message["type"] == "error"
    assert "message" in error_message


def test_audio_frame_validation(sample_pcm_audio):
    assert isinstance(sample_pcm_audio, bytes)
    assert len(sample_pcm_audio) > 0
    
    expected_length = 16000 * 2
    assert len(sample_pcm_audio) == expected_length
