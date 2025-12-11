import pytest
import asyncio
from meet_transcriber.session_manager import SessionManager
from meet_transcriber.transcriber import AudioTranscriber


@pytest.mark.asyncio
async def test_session_manager_integration():
    manager = SessionManager(max_concurrent_sessions=2)
    
    session1 = await manager.create_session({"user": "user1"})
    session2 = await manager.create_session({"user": "user2"})
    
    assert await manager.get_active_session_count() == 2
    
    assert session1.participant_info["user"] == "user1"
    assert session2.participant_info["user"] == "user2"
    
    await session1.audio_queue.put(b"test_audio_data")
    audio_data = await session1.audio_queue.get()
    assert audio_data == b"test_audio_data"
    
    await manager.end_session(session1.session_id)
    assert await manager.get_active_session_count() == 1
    
    await manager.end_session(session2.session_id)
    assert await manager.get_active_session_count() == 0


@pytest.mark.asyncio
async def test_transcriber_initialization():
    transcripts = []
    
    def on_transcript(text: str, is_final: bool):
        transcripts.append((text, is_final))
    
    transcriber = AudioTranscriber(
        model_name="tiny.en",
        language="en",
        on_transcript=on_transcript
    )
    
    assert transcriber.model_name == "tiny.en"
    assert transcriber.language == "en"
    assert transcriber.on_transcript is not None


@pytest.mark.asyncio
async def test_audio_queue_flow(sample_pcm_audio):
    queue = asyncio.Queue()
    
    await queue.put(sample_pcm_audio)
    await queue.put(None)
    
    received_data = await queue.get()
    assert received_data == sample_pcm_audio
    
    stop_signal = await queue.get()
    assert stop_signal is None
