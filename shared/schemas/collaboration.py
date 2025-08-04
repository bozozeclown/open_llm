# shared/schemas/collaboration.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID

class SessionRole(str, Enum):
    """Roles in collaboration sessions."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(str, Enum):
    """Permissions in collaboration sessions."""
    READ = "read"
    WRITE = "write"
    SHARE = "share"
    MANAGE = "manage"

class Collaborator(BaseModel):
    """Collaborator in a session."""
    id: str
    name: str
    role: SessionRole
    permissions: List[Permission]
    joined_at: datetime
    last_active: datetime
    is_active: bool = True
    
    @validator('permissions')
    def validate_permissions(cls, v, values):
        """Validate permissions based on role."""
        role = values.get('role', SessionRole.VIEWER)
        
        role_permissions = {
            SessionRole.OWNER: [Permission.READ, Permission.WRITE, Permission.SHARE, Permission.MANAGE],
            SessionRole.EDITOR: [Permission.READ, Permission.WRITE, Permission.SHARE],
            SessionRole.VIEWER: [Permission.READ],
            SessionRole.GUEST: [Permission.READ]
        }
        
        required_permissions = set(role_permissions.get(role, []))
        provided_permissions = set(v)
        
        if not required_permissions.issubset(provided_permissions):
            raise ValueError(f"Insufficient permissions for role {role}")
        
        return v

class Session(BaseModel):
    """Collaboration session."""
    id: str = Field(default_factory=lambda: str(UUID.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    owner_id: str
    code: str = Field(..., min_length=1)
    language: str = Field(..., min_length=2, max_length=20)
    collaborators: Dict[str, Collaborator] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    is_public: bool = False
    is_active: bool = True
    max_collaborators: int = Field(default=10, ge=1, le=100)
    
    @validator('collaborators')
    def validate_collaborators(cls, v, values):
        """Validate collaborators."""
        owner_id = values.get('owner_id')
        
        # Ensure owner is in collaborators
        if owner_id not in v:
            raise ValueError("Owner must be in collaborators list")
        
        # Ensure owner has correct role and permissions
        owner = v[owner_id]
        if owner.role != SessionRole.OWNER:
            raise ValueError("Owner must have OWNER role")
        
        if Permission.MANAGE not in owner.permissions:
            raise ValueError("Owner must have MANAGE permission")
        
        # Check collaborator count limit
        if len(v) > values.get('max_collaborators', 10):
            raise ValueError("Exceeded maximum number of collaborators")
        
        return v
    
    def add_collaborator(self, collaborator: Collaborator) -> bool:
        """Add a collaborator to the session."""
        if len(self.collaborators) >= self.max_collaborators:
            return False
        
        self.collaborators[collaborator.id] = collaborator
        self.last_modified = datetime.utcnow()
        return True
    
    def remove_collaborator(self, collaborator_id: str) -> bool:
        """Remove a collaborator from the session."""
        if collaborator_id == self.owner_id:
            return False  # Cannot remove owner
        
        if collaborator_id in self.collaborators:
            del self.collaborators[collaborator_id]
            self.last_modified = datetime.utcnow()
            return True
        
        return False
    
    def update_code(self, code: str, collaborator_id: str) -> bool:
        """Update session code."""
        collaborator = self.collaborators.get(collaborator_id)
        if not collaborator:
            return False
        
        if Permission.WRITE not in collaborator.permissions:
            return False
        
        self.code = code
        self.last_modified = datetime.utcnow()
        return True
    
    def get_collaborator_count(self) -> int:
        """Get number of active collaborators."""
        return len([c for c in self.collaborators.values() if c.is_active])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'code': self.code,
            'language': self.language,
            'collaborators': {k: v.dict() for k, v in self.collaborators.items()},
            '