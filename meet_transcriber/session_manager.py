import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    session_id: UUID
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    audio_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    participant_info: Dict = field(default_factory=dict)
    is_active: bool = True


class SessionManager:
    def __init__(self, max_concurrent_sessions: int):
        self.max_concurrent_sessions = max_concurrent_sessions
        self._sessions: Dict[UUID, SessionMetadata] = {}
        self._lock = asyncio.Lock()
        
    async def create_session(self, participant_info: Optional[Dict] = None) -> SessionMetadata:
        async with self._lock:
            if len(self._sessions) >= self.max_concurrent_sessions:
                raise ValueError(
                    f"Maximum concurrent sessions ({self.max_concurrent_sessions}) reached"
                )
            
            session_id = uuid4()
            metadata = SessionMetadata(
                session_id=session_id,
                participant_info=participant_info or {},
            )
            self._sessions[session_id] = metadata
            logger.info(f"Created session {session_id}")
            return metadata
    
    async def get_session(self, session_id: UUID) -> Optional[SessionMetadata]:
        return self._sessions.get(session_id)
    
    async def update_activity(self, session_id: UUID) -> None:
        session = await self.get_session(session_id)
        if session:
            session.last_activity = datetime.utcnow()
    
    async def end_session(self, session_id: UUID) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_active = False
                await session.audio_queue.put(None)
                del self._sessions[session_id]
                logger.info(f"Ended session {session_id}")
    
    async def get_active_session_count(self) -> int:
        return len([s for s in self._sessions.values() if s.is_active])
    
    async def cleanup_inactive_sessions(self, timeout_seconds: int = 300) -> None:
        async with self._lock:
            now = datetime.utcnow()
            to_remove = []
            for session_id, session in self._sessions.items():
                elapsed = (now - session.last_activity).total_seconds()
                if elapsed > timeout_seconds:
                    to_remove.append(session_id)
            
            for session_id in to_remove:
                session = self._sessions.get(session_id)
                if session:
                    session.is_active = False
                    await session.audio_queue.put(None)
                    del self._sessions[session_id]
                    logger.warning(f"Cleaned up inactive session {session_id}")
