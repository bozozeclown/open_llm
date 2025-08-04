# core/collaboration/session_manager.py
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class SessionRole(Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    SHARE = "share"

@dataclass
class Collaborator:
    id: str
    name: str
    role: SessionRole
    permissions: List[Permission]
    joined_at: datetime
    last_active: datetime

@dataclass
class Session:
    id: str
    name: str
    owner_id: str
    code: str
    language: str
    collaborators: Dict[str, Collaborator]
    created_at: datetime
    last_modified: datetime
    is_public: bool

class CollaborationManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        self.websocket_connections: Dict[str, Any] = {}  # session_id -> websocket connections
    
    async def create_session(self, owner_id: str, name: str, code: str, language: str, is_public: bool = False) -> Session:
        """Create a new collaboration session"""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            name=name,
            owner_id=owner_id,
            code=code,
            language=language,
            collaborators={},
            created_at=datetime.now(),
            last_modified=datetime.now(),
            is_public=is_public
        )
        
        # Add owner as collaborator
        owner_collaborator = Collaborator(
            id=owner_id,
            name="Owner",
            role=SessionRole.OWNER,
            permissions=list(Permission),
            joined_at=datetime.now(),
            last_active=datetime.now()
        )
        session.collaborators[owner_id] = owner_collaborator
        
        self.sessions[session_id] = session
        
        # Update user sessions
        if owner_id not in self.user_sessions:
            self.user_sessions[owner_id] = []
        self.user_sessions[owner_id].append(session_id)
        
        return session
    
    async def join_session(self, session_id: str, user_id: str, user_name: str) -> Optional[Session]:
        """Join an existing collaboration session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if user is already a collaborator
        if user_id not in session.collaborators:
            # Add as viewer by default
            collaborator = Collaborator(
                id=user_id,
                name=user_name,
                role=SessionRole.VIEWER,
                permissions=[Permission.READ],
                joined_at=datetime.now(),
                last_active=datetime.now()
            )
            session.collaborators[user_id] = collaborator
        
        # Update user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        if session_id not in self.user_sessions[user_id]:
            self.user_sessions[user_id].append(session_id)
        
        return session
    
    async def leave_session(self, session_id: str, user_id: str) -> bool:
        """Leave a collaboration session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Remove collaborator (but keep owner)
        if user_id != session.owner_id and user_id in session.collaborators:
            del session.collaborators[user_id]
        
        # Update user sessions
        if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
            self.user_sessions[user_id].remove(session_id)
        
        # Delete session if no collaborators left
        if len(session.collaborators) <= 1:
            del self.sessions[session_id]
        
        return True
    
    async def update_code(self, session_id: str, user_id: str, code: str, cursor_position: int = None) -> bool:
        """Update code in a collaboration session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        collaborator = session.collaborators.get(user_id)
        
        # Check permissions
        if not collaborator or Permission.WRITE not in collaborator.permissions:
            return False
        
        # Update code
        session.code = code
        session.last_modified = datetime.now()
        collaborator.last_active = datetime.now()
        
        # Broadcast to other collaborators
        await self._broadcast_code_update(session_id, user_id, code, cursor_position)
        
        return True
    
    async def _broadcast_code_update(self, session_id: str, user_id: str, code: str, cursor_position: int = None):
        """Broadcast code update to all collaborators in the session"""
        if session_id not in self.websocket_connections:
            return
        
        message = {
            "type": "code_update",
            "user_id": user_id,
            "code": code,
            "cursor_position": cursor_position,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected websockets except the sender
        for connection in self.websocket_connections[session_id]:
            if connection.user_id != user_id:
                await connection.send_json(message)
    
    async def add_websocket_connection(self, session_id: str, user_id: str, websocket):
        """Add a websocket connection to a session"""
        if session_id not in self.websocket_connections:
            self.websocket_connections[session_id] = []
        
        self.websocket_connections[session_id].append(websocket)
        
        # Send current state to the new connection
        session = self.sessions.get(session_id)
        if session:
            await websocket.send_json({
                "type": "session_state",
                "session": asdict(session),
                "timestamp": datetime.now().isoformat()
            })
    
    async def remove_websocket_connection(self, session_id: str, websocket):
        """Remove a websocket connection from a session"""
        if session_id in self.websocket_connections:
            if websocket in self.websocket_connections[session_id]:
                self.websocket_connections[session_id].remove(websocket)
    
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[session_id] for session_id in session_ids if session_id in self.sessions]
    
    async def get_public_sessions(self, limit: int = 50) -> List[Session]:
        """Get public sessions"""
        public_sessions = [session for session in self.sessions.values() if session.is_public]
        return sorted(public_sessions, key=lambda x: x.last_modified, reverse=True)[:limit]