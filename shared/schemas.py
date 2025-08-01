from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class CompletionRequest(BaseModel):
    context: str  # Full file content
    cursor_context: str  # Line/fragment near cursor
    
class SignatureHelp(BaseModel):
    name: str
    parameters: List[Dict[str, str]]
    active_parameter: int

class SignatureRequest(BaseModel):
    code: str
    language: str
    cursor_pos: int
    
class HealthStatus(BaseModel):
    service: str
    status: Literal["online", "degraded", "offline"]
    models: List[str] = []
    latency: Optional[float]

class IntegrationConfig(BaseModel):
    priority: int
    timeout: int = 30
    
class Query(BaseModel):
    """Enhanced query class with routing support"""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Add these new methods
    def with_additional_context(self, reasoning_data: Dict) -> 'Query':
        """
        Create a new query instance with reasoning context
        Usage:
            enriched_query = original_query.with_additional_context(
                {"source": "graph", "confidence": 0.9}
            )
        """
        return self.copy(
            update={
                "metadata": {
                    **self.metadata,
                    "reasoning": reasoning_data
                }
            }
        )
    
    @property
    def preferred_provider(self) -> Optional[str]:
        """Get preferred LLM provider if specified"""
        return self.metadata.get('preferred_provider')
    
    @preferred_provider.setter
    def preferred_provider(self, provider: str):
        """Set preferred LLM provider"""
        self.metadata['preferred_provider'] = provider
        
class FeedbackRating(BaseModel):
    query_hash: str
    response_hash: str
    rating: float = Field(..., ge=0, le=5)
    comment: Optional[str]
    
class FeedbackCorrection(BaseModel):
    node_id: str
    corrected_content: str
    severity: Literal["low", "medium", "high"] = "medium"