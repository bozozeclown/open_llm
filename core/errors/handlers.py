# core/errors/handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorResponse:
    @staticmethod
    def create_error_response(
        status_code: int,
        error_type: str,
        message: str,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        return {
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        }

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.create_error_response(
            status_code=422,
            error_type="validation_error",
            message="Request validation failed",
            details={"errors": exc.errors()}
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.create_error_response(
            status_code=exc.status_code,
            error_type="http_error",
            message=exc.detail,
            details={"headers": dict(exc.headers)}
        )
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.create_error_response(
            status_code=500,
            error_type="internal_error",
            message="An unexpected error occurred",
            details={"trace_id": str(id(request))}
        )
    )

# core/errors/resilience.py
import asyncio
from functools import wraps
from typing import Callable, Any, Dict, Optional
import time

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                
                raise e
        
        return wrapper

class RetryHandler:
    def __init__(self, max_retries=3, backoff_factor=1):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def retry(self, exceptions: tuple = (Exception,)):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(self.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < self.max_retries:
                            delay = self.backoff_factor * (2 ** attempt)
                            await asyncio.sleep(delay)
                        else:
                            break
                
                raise last_exception
            
            return wrapper
        return decorator