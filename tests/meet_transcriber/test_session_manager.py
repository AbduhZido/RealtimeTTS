import asyncio
import pytest
from datetime import datetime, timedelta

from meet_transcriber.session_manager import SessionManager


@pytest.mark.asyncio
async def test_create_session():
    manager = SessionManager(max_concurrent_sessions=5)
    
    session = await manager.create_session({"user_id": "test123"})
    
    assert session is not None
    assert session.session_id is not None
    assert session.participant_info["user_id"] == "test123"
    assert session.is_active is True
    assert isinstance(session.audio_queue, asyncio.Queue)


@pytest.mark.asyncio
async def test_max_concurrent_sessions():
    manager = SessionManager(max_concurrent_sessions=2)
    
    session1 = await manager.create_session()
    session2 = await manager.create_session()
    
    with pytest.raises(ValueError, match="Maximum concurrent sessions"):
        await manager.create_session()
    
    await manager.end_session(session1.session_id)
    
    session3 = await manager.create_session()
    assert session3 is not None


@pytest.mark.asyncio
async def test_get_session():
    manager = SessionManager(max_concurrent_sessions=5)
    
    created_session = await manager.create_session()
    retrieved_session = await manager.get_session(created_session.session_id)
    
    assert retrieved_session is not None
    assert retrieved_session.session_id == created_session.session_id


@pytest.mark.asyncio
async def test_update_activity():
    manager = SessionManager(max_concurrent_sessions=5)
    
    session = await manager.create_session()
    original_time = session.last_activity
    
    await asyncio.sleep(0.1)
    await manager.update_activity(session.session_id)
    
    assert session.last_activity > original_time


@pytest.mark.asyncio
async def test_end_session():
    manager = SessionManager(max_concurrent_sessions=5)
    
    session = await manager.create_session()
    session_id = session.session_id
    
    await manager.end_session(session_id)
    
    retrieved_session = await manager.get_session(session_id)
    assert retrieved_session is None


@pytest.mark.asyncio
async def test_get_active_session_count():
    manager = SessionManager(max_concurrent_sessions=5)
    
    assert await manager.get_active_session_count() == 0
    
    session1 = await manager.create_session()
    assert await manager.get_active_session_count() == 1
    
    session2 = await manager.create_session()
    assert await manager.get_active_session_count() == 2
    
    await manager.end_session(session1.session_id)
    assert await manager.get_active_session_count() == 1


@pytest.mark.asyncio
async def test_cleanup_inactive_sessions():
    manager = SessionManager(max_concurrent_sessions=5)
    
    session = await manager.create_session()
    
    session.last_activity = datetime.utcnow() - timedelta(seconds=4)
    
    await manager.cleanup_inactive_sessions(timeout_seconds=3)
    
    retrieved_session = await manager.get_session(session.session_id)
    assert retrieved_session is None
