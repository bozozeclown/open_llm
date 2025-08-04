# shared/schemas/response.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime

class ResponseType(str, Enum):
    """Types of responses."""
    TEXT = "text"
    CODE = "code"
    ANALYSIS = "analysis"
    SUGGESTIONS = "suggestions"
    ERROR = "error"
    STATUS = "status"
    METADATA = "metadata"

class SourceType(str, Enum):
    """Sources of responses."""
    KNOWLEDGE_GRAPH = "knowledge_graph"
    RULE_ENGINE = "rule_engine"
    LLM = "llm"
    CACHE = "cache"
    HYBRID = "hybrid"

class ProcessingMetadata(BaseModel):
    """Processing metadata for responses."""
    source: SourceType
    provider: Optional[str] = None
    model: Optional[str] = None
    processing_time: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tokens_used: Optional[int] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0.0)
    cache_hit: bool = False
    sla_tier: Optional[str] = None
    reasoning_path: Optional[str] = None
    
class ResponseMetadata(BaseModel):
    """Response metadata."""
    processing: ProcessingMetadata
    context_used: bool = False
    related_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    visualization: Optional[Dict[str, Any]] = None
    version_id: Optional[str] = None
    
    @validator('metrics')
    def validate_metrics(cls, v):
        """Validate metrics."""
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Metric keys must be strings")
            if not isinstance(value, (int, float, bool, str, list, dict)):
                raise ValueError(f"Invalid metric value type for key '{key}'")
        return v

class Response(BaseModel):
    """Main response model."""
    content: str
    response_type: ResponseType = ResponseType.TEXT
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate response content."""
        if not v or not v.strip():
            raise ValueError("Response content cannot be empty")
        return v.strip()
    
    @validator('metadata')
    def validate_metadata(cls, v, values):
        """Validate metadata consistency."""
        processing = v.get('processing', {})
        
        # If cache_hit is True, source should be CACHE
        if processing.get('cache_hit') and processing.get('source') != SourceType.CACHE:
            raise ValueError("Cache hit requires source to be CACHE")
        
        return v
    
    def is_error(self) -> bool:
        """Check if response is an error."""
        return self.response_type == ResponseType.ERROR
    
    def get_processing_time(self) -> Optional[float]:
        """Get processing time."""
        return self.metadata.processing.processing_time
    
    def get_confidence(self) -> float:
        """Get confidence score."""
        return self.confidence
    
    def add_suggestion(self, suggestion: Dict[str, Any]) -> None:
        """Add a suggestion to response metadata."""
        self.metadata.suggestions.append(suggestion)
    
    def add_metric(self, key: str, value: Any) -> None:
        """Add a metric to response metadata."""
        self.metadata.metrics[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'content': self.content,
            'response_type': self.response_type.value,
            'confidence': self.confidence,
            'metadata': self.metadata.dict()
        }

class CodeResponse(Response):
    """Code-specific response."""
    response_type: ResponseType = ResponseType.CODE
    language: Optional[str] = None
    file_path: Optional[str] = None
    line_range: Optional[Dict[str, int]] = None
    
    @validator('line_range')
    def validate_line_range(cls, v):
        """Validate line range."""
        if v is not None:
            if 'start' not in v or 'end' not in v:
                raise ValueError("Line range must include 'start' and 'end'")
            if v['start'] > v['end']:
                raise ValueError("Line range start must be less than or equal to end")
        return v

class AnalysisResponse(Response):
    """Analysis-specific response."""
    response_type: ResponseType = ResponseType.ANALYSIS
    analysis_type: Optional[str] = None
    complexity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    security_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    issues_found: int = 0
    suggestions_count: int = 0

class ErrorResponse(Response):
    """Error-specific response."""
    response_type: ResponseType = ResponseType.ERROR
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_possible: bool = True
    
    @validator('error_message')
    def validate_error_message(cls, v):
        """Validate error message."""
        if v and len(v) > 1000:
            raise ValueError("Error message too long (max 1000 characters)")
        return v

class BatchResponse(BaseModel):
    """Batch response model."""
    responses: List[Union[Response, CodeResponse, AnalysisResponse, ErrorResponse]]
    batch_id: Optional[str] = None
    total_processing_time: Optional[float] = None
    success_count: int = 0
    error_count: int = 0
    
    @validator('responses')
    def validate_responses(cls, v):
        """Validate batch responses."""
        if not v:
            raise ValueError("Batch responses cannot be empty")
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 responses")
        
        # Count successes and errors
        success_count = sum(1 for r in v if not isinstance(r, ErrorResponse))
        error_count = len(v) - success_count
        
        return v
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if not self.responses:
            return 0.0
        return self.success_count / len(self.responses)
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence."""
        if not self.responses:
            return 0.0
        
        confidences = [r.confidence for r in self.responses if hasattr(r, 'confidence')]
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)