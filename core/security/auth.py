# core/security/auth.py
from fastapi import HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import secrets
import time
from collections import defaultdict, deque

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Simple in-memory API key storage (use database in production)
VALID_API_KEYS = {"dev-key-123", "prod-key-456"}

# Rate limiting
class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, api_key: str) -> bool:
        now = time.time()
        key_requests = self.requests[api_key]
        
        # Remove old requests
        while key_requests and key_requests[0] <= now - self.window_seconds:
            key_requests.popleft()
        
        # Check if under limit
        if len(key_requests) >= self.max_requests:
            return False
        
        key_requests.append(now)
        return True

rate_limiter = RateLimiter()

async def get_api_key(api_key: Optional[str] = Depends(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    
    if not rate_limiter.is_allowed(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return api_key

# core/security/authorization.py
from enum import Enum
from typing import List, Set

class Permission(Enum):
    QUERY = "query"
    FEEDBACK = "feedback"
    ADMIN = "admin"

class Role:
    def __init__(self, permissions: Set[Permission]):
        self.permissions = permissions

# Role definitions
ROLES = {
    "user": Role({Permission.QUERY}),
    "premium_user": Role({Permission.QUERY, Permission.FEEDBACK}),
    "admin": Role({Permission.QUERY, Permission.FEEDBACK, Permission.ADMIN})
}

# User roles (in production, store in database)
USER_ROLES = {
    "user1": "user",
    "premium_user1": "premium_user",
    "admin1": "admin"
}

async def check_permission(api_key: str, required_permission: Permission):
    """Check if user has required permission"""
    username = USER_ROLES.get(api_key, "user")
    user_role = ROLES.get(username, Role(set()))
    
    if required_permission not in user_role.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return True