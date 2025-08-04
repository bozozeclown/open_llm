{\rtf1}# core/security/rate_limiter.py
import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

class RateLimitType(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"

@dataclass
class RateLimitRule:
    name: str
    limit: int  # Max requests
    window: int  # Time window in seconds
    type: RateLimitType
    burst: int = 1  # Burst capacity (for token bucket)

class AdvancedRateLimiter:
    def __init__(self):
        self.rules: Dict[str, RateLimitRule] = {}
        self.user_requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.user_tokens: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.last_cleanup = time.time()
    
    def add_rule(self, name: str, limit: int, window: int, 
                 rate_type: RateLimitType = RateLimitType.SLIDING_WINDOW, burst: int = 1):
        """Add a rate limiting rule"""
        self.rules[name] = RateLimitRule(name, limit, window, rate_type, burst)
    
    async def check_rate_limit(self, user_id: str, rule_name: str) -> Tuple[bool, Optional[str]]:
        """Check if user is rate limited"""
        if rule_name not in self.rules:
            return True, None  # No rule = no limit
        
        rule = self.rules[rule_name]
        
        # Cleanup old data periodically
        if time.time() - self.last_cleanup > 60:  # Cleanup every minute
            self._cleanup_old_requests()
            self.last_cleanup = time.time()
        
        if rule.type == RateLimitType.FIXED_WINDOW:
            return await self._check_fixed_window(user_id, rule)
        elif rule.type == RateLimitType.SLIDING_WINDOW:
            return await self._check_sliding_window(user_id, rule)
        elif rule.type == RateLimitType.TOKEN_BUCKET:
            return await self._check_token_bucket(user_id, rule)
        
        return True, None
    
    async def _check_fixed_window(self, user_id: str, rule: RateLimitRule) -> Tuple[bool, Optional[str]]:
        """Check fixed window rate limiting"""
        now = time.time()
        window_start = now - rule.window
        
        # Remove old requests
        user_queue = self.user_requests[user_id][rule.name]
        while user_queue and user_queue[0] < window_start:
            user_queue.popleft()
        
        # Check if limit exceeded
        if len(user_queue) >= rule.limit:
            return False, f"Rate limit exceeded: {rule.limit} requests per {rule.window} seconds"
        
        # Add current request
        user_queue.append(now)
        return True, None
    
    async def _check_sliding_window(self, user_id: str, rule: RateLimitRule) -> Tuple[bool, Optional[str]]:
        """Check sliding window rate limiting"""
        now = time.time()
        window_start = now - rule.window
        
        # Remove old requests
        user_queue = self.user_requests[user_id][rule.name]
        while user_queue and user_queue[0] < window_start:
            user_queue.popleft()
        
        # Check if limit exceeded
        if len(user_queue) >= rule.limit:
            return False, f"Rate limit exceeded: {rule.limit} requests per {rule.window} seconds"
        
        # Add current request
        user_queue.append(now)
        return True, None
    
    async def _check_token_bucket(self, user_id: str, rule: RateLimitRule) -> Tuple[bool, Optional[str]]:
        """Check token bucket rate limiting"""
        now = time.time()
        tokens = self.user_tokens[user_id][rule.name]
        
        # Add tokens based on refill rate
        refill_rate = rule.limit / rule.window
        time_since_last_check = now - self.last_cleanup
        tokens = min(tokens + refill_rate * time_since_last_check, rule.burst)
        
        # Check if tokens available
        if tokens >= 1:
            self.user_tokens[user_id][rule.name] = tokens - 1
            return True, None
        else:
            return False, f"Rate limit exceeded: token bucket empty"
    
    def _cleanup_old_requests(self):
        """Clean up old request data"""
        now = time.time()
        
        for user_id, user_rules in self.user_requests.items():
            for rule_name, requests in user_rules.items():
                rule = self.rules.get(rule_name)
                if rule:
                    window_start = now - rule.window
                    while requests and requests[0] < window_start:
                        requests.popleft()
    
    def get_user_status(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status for a user"""
        status = {}
        
        for rule_name, rule in self.rules.items():
            user_requests = self.user_requests[user_id][rule_name]
            user_tokens = self.user_tokens[user_id][rule_name]
            
            now = time.time()
            window_start = now - rule.window
            
            # Count requests in current window
            recent_requests = sum(1 for req_time in user_requests if req_time >= window_start)
            
            status[rule_name] = {
                "rule_type": rule.type.value,
                "limit": rule.limit,
                "window": rule.window,
                "current_requests": recent_requests,
                "remaining_capacity": rule.limit - recent_requests,
                "tokens": user_tokens if rule.type == RateLimitType.TOKEN_BUCKET else None
            }
        
        return status

# Integration with FastAPI
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-KEY")

rate_limiter = AdvancedRateLimiter()

# Configure rate limiting rules
rate_limiter.add_rule("api_requests", 100, 60, RateLimitType.SLIDING_WINDOW)
rate_limiter.add_rule("code_analysis", 10, 60, RateLimitType.TOKEN_BUCKET, burst=5)
rate_limiter.add_rule("multimodal_analysis", 5, 60, RateLimitType.FIXED_WINDOW)

async def get_rate_limit_user(request: Request):
    """Extract user identifier from request"""
    # In a real implementation, this would extract from JWT or API key
    return request.headers.get("X-API-KEY", "anonymous")

async def rate_limit_dependency(request: Request, rule_name: str = "api_requests"):
    """FastAPI dependency for rate limiting"""
    user_id = await get_rate_limit_user(request)
    is_allowed, message = await rate_limiter.check_rate_limit(user_id, rule_name)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={"Retry-After": "60"}
        )
    
    return user_id