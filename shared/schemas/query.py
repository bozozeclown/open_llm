# shared/schemas/query.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime

class QueryType(str, Enum):
    """Types of queries supported by the system."""
    CODE_ANALYSIS = "code_analysis"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    EXPLANATION = "explanation"
    COMPLETION = "completion"
    TRANSLATION = "translation"
    GENERATION = "generation"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    TESTING = "testing"

class PriorityLevel(str, Enum):
    """Priority levels for queries."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class QueryContext(BaseModel):
    """Context information for a query."""
    code: Optional[str] = None
    language: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cursor_position: Optional[int] = None
    project_structure: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, str]] = None
    functions: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    imports: Optional[List[str]] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded image data
    session_id: Optional[str] = None
    version_id: Optional[str] = None

class QueryMetadata(BaseModel):
    """Metadata for a query."""
    query_type: QueryType = QueryType.EXPLANATION
    priority: PriorityLevel = PriorityLevel.NORMAL
    language: Optional[str] = None
    complexity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    require_quality: bool = False
    allow_batching: bool = True
    force_online: bool = False
    timeout: Optional[int] = Field(None, gt=0)
    max_tokens: Optional[int] = Field(None, gt=0)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: str = "api"  # api, cli, web, mobile, voice
    preferred_provider: Optional[str] = None
    sla_tier: Optional[str] = None

class Query(BaseModel):
    """Main query model."""
    content: str = Field(..., min_length=1, max_length=10000)
    context: QueryContext = Field(default_factory=QueryContext)
    metadata: QueryMetadata = Field(default_factory=QueryMetadata)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate query content."""
        if not v.strip():
            raise ValueError("Query content cannot be empty")
        return v.strip()
    
    @validator('metadata')
    def validate_metadata(cls, v, values):
        """Validate metadata consistency."""
        context = values.get('context', {})
        
        # If image data is provided, validate it's base64
        if context.get('image_data'):
            try:
                import base64
                # Check if it's valid base64
                base64.b64decode(context['image_data'])
            except Exception:
                raise ValueError("Invalid image data format")
        
        # Validate language if provided
        if v.get('language') and context.get('language'):
            if v['language'] != context['language']:
                raise ValueError("Language mismatch between metadata and context")
        
        return v
    
    def get_hash(self) -> str:
        """Get a hash of the query for caching."""
        import hashlib
        content = f"{self.content}:{self.metadata.query_type}:{self.metadata.language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def estimate_complexity(self) -> float:
        """Estimate query complexity (0.0 to 1.0)."""
        complexity = 0.0
        
        # Base complexity from content length
        content_length = len(self.content)
        complexity += min(content_length / 1000, 0.3)
        
        # Context complexity
        if self.context.code:
            complexity += 0.2
        if self.context.error_message:
            complexity += 0.3
        if self.context.image_data:
            complexity += 0.2
        
        # Metadata complexity
        if self.metadata.require_quality:
            complexity += 0.1
        if self.metadata.priority == PriorityLevel.CRITICAL:
            complexity += 0.1
        
        return min(complexity, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary."""
        return {
            'content': self.content,
            'context': self.context.dict(),
            'metadata': self.metadata.dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Query':
        """Create query from dictionary."""
        return cls(
            content=data['content'],
            context=QueryContext(**data.get('context', {})),
            metadata=QueryMetadata(**data.get('metadata', {}))
        )

class BatchQuery(BaseModel):
    """Batch query model for processing multiple queries."""
    queries: List[Query]
    batch_id: Optional[str] = None
    timeout: Optional[int] = Field(None, gt=0)
    
    @validator('queries')
    def validate_queries(cls, v):
        """Validate batch queries."""
        if not v:
            raise ValueError("Batch queries cannot be empty")
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 queries")
        return v

class QueryResponse(BaseModel):
    """Query response model."""
    query_id: Optional[str] = None
    content: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'query_id': self.query_id,
            'content': self.content,
            'confidence': self.confidence,
            'sources': self.sources,
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }

class BatchResponse(BaseModel):
    """Batch response model."""
    batch_id: Optional[str] = None
    responses: List[QueryResponse]
    total_processing_time: Optional[float] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)