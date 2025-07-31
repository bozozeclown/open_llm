from modules.base_module import BaseModule
from shared.schemas import Response, Query

class GenericCodeModule(BaseModule):
    MODULE_ID = "code_generic"
    VERSION = "0.1.0"
    
    async def initialize(self):
        self._ready = True
        
    async def process(self, query: Query) -> Response:
        """Fallback processing for all code requests"""
        return Response(
            content=f"Generic code processing: {query.content[:200]}...",
            metadata={
                "module": self.MODULE_ID,
                "fallback": True,
                "warning": "Primary module unavailable"
            },
            metrics={"generic_processing": 1.0}
        )
        
    def health_check(self) -> dict:
        return {
            "status": "ready",
            "version": self.VERSION,
            "features": ["basic_code_processing"]
        }

class GenericChatModule(BaseModule):
    MODULE_ID = "chat_generic"
    VERSION = "0.1.0"
    
    async def initialize(self):
        self._ready = True
        
    async def process(self, query: Query) -> Response:
        """Fallback processing for all requests"""
        return Response(
            content=f"Generic response: {query.content[:150]}...",
            metadata={
                "module": self.MODULE_ID,
                "fallback": True
            },
            metrics={"generic_response": 1.0}
        )
        
    def health_check(self) -> dict:
        return {
            "status": "ready",
            "version": self.VERSION,
            "features": ["basic_text_processing"]
        }