from pydantic import BaseModel

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