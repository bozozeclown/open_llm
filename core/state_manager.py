from typing import Dict, Any
from shared.schemas import Query, Response

class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context = {}
        self.history = []
        
    def update(self, query: Query, response: Response):
        self.history.append((query, response))
        self._update_context(query, response)
        
    def _update_context(self, query: Query, response: Response):
        """Extract and store relevant context"""
        self.context.update({
            "last_module": response.metadata.get("module"),
            "last_type": query.content_type
        })

class StateManager:
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        
    def get_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id)
        return self.sessions[session_id]