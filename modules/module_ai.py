from modules.base_module import BaseModule
from core.integrations.manager import IntegrationManager

class AIModule(BaseModule):
    MODULE_ID = "ai_integration"
    CAPABILITIES = ["text_generation"]
    
    def __init__(self):
        self.integrations = {}
    
    async def initialize(self):
        # Initialize configured integrations
        self.integrations["ollama"] = IntegrationManager.get_integration("ollama")
        # Add others from config
        
    async def process(self, query: Query) -> Response:
        integration = self.integrations.get(query.metadata.get("integration"))
        if not integration:
            return Response.error("Integration not configured")
        
        try:
            result = integration.generate(
                query.content,
                **query.metadata.get("params", {})
            )
            return Response(content=result)
        except Exception as e:
            return Response.error(f"Generation failed: {str(e)}")