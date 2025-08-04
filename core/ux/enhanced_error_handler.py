# core/ux/enhanced_error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any, Optional
import traceback
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EnhancedErrorHandler:
    def __init__(self):
        self.error_templates = {
            "validation_error": {
                "title": "Invalid Request",
                "message": "The request contains invalid data.",
                "suggestions": [
                    "Check your request format",
                    "Ensure all required fields are provided",
                    "Verify data types match expected formats"
                ]
            },
            "rate_limit_exceeded": {
                "title": "Too Many Requests",
                "message": "You've exceeded the rate limit.",
                "suggestions": [
                    "Wait a moment before trying again",
                    "Consider upgrading your plan for higher limits",
                    "Batch multiple requests into one"
                ]
            },
            "internal_error": {
                "title": "Internal Server Error",
                "message": "Something went wrong on our end.",
                "suggestions": [
                    "Please try again later",
                    "Contact support if the problem persists",
                    "Check our status page for system updates"
                ]
            }
        }
    
    async def handle_error(self, request: Request, error: Exception) -> JSONResponse:
        """Handle errors with enhanced user feedback"""
        error_id = str(id(request))
        timestamp = datetime.now().isoformat()
        
        # Log the error
        logger.error(f"Error {error_id}: {str(error)}")
        logger.error(traceback.format_exc())
        
        # Determine error type
        error_type = self._classify_error(error)
        template = self.error_templates.get(error_type, self.error_templates["internal_error"])
        
        # Create error response
        error_response = {
            "error": {
                "id": error_id,
                "type": error_type,
                "title": template["title"],
                "message": template["message"],
                "timestamp": timestamp,
                "path": str(request.url),
                "method": request.method,
                "suggestions": template["suggestions"]
            }
        }
        
        # Add debugging info for developers
        if isinstance(error, RequestValidationError):
            error_response["error"]["details"] = {
                "validation_errors": error.errors(),
                "body": error.body
            }
        
        # Set appropriate status code
        status_code = self._get_status_code(error)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={"X-Error-ID": error_id}
        )
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate handling"""
        if isinstance(error, RequestValidationError):
            return "validation_error"
        elif isinstance(error, HTTPException) and error.status_code == 429:
            return "rate_limit_exceeded"
        else:
            return "internal_error"
    
    def _get_status_code(self, error: Exception) -> int:
        """Get appropriate HTTP status code"""
        if isinstance(error, HTTPException):
            return error.status_code
        elif isinstance(error, RequestValidationError):
            return 422
        else:
            return 500

# Integration with FastAPI app
error_handler = EnhancedErrorHandler()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await error_handler.handle_error(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await error_handler.handle_error(request, exc)