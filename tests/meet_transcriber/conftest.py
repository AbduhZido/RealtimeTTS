import asyncio
import numpy as np
import pytest
import wave
import tempfile
import os


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_pcm_audio():
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(frequency * 2 * np.pi * t)
    
    audio_int16 = (audio * 32767).astype(np.int16)
    
    return audio_int16.tobytes()


@pytest.fixture
def sample_wav_file(sample_pcm_audio):
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(sample_pcm_audio)
        
        yield f.name
    
    try:
        os.unlink(f.name)
    except:
        pass


@pytest.fixture
def mock_settings():
    from meet_transcriber.config import Settings
    return Settings(
        model_name="tiny.en",
        language="en",
        auth_token="test_token",
        max_concurrent_sessions=5,
        host="127.0.0.1",
        port=8765,
        log_level="DEBUG",
    )
