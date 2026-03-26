"""Dashboard Pydantic models"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CallRecord(BaseModel):
    """Single probe or invocation record"""
    tool: str
    provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["ok", "error", "timeout"] = "ok"
    response_time_ms: float = 0.0
    error: Optional[str] = None
    source: Literal["probe", "invoke"] = "probe"


class ToolStats(BaseModel):
    """Aggregated stats for a tool x provider pair"""
    tool: str
    provider: str
    total_calls: int = 0
    success_count: int = 0
    success_rate: float = 0.0
    avg_response_ms: float = 0.0
    last_status: Optional[str] = None
    last_check_time: Optional[datetime] = None
    last_error: Optional[str] = None


class ToolInfo(BaseModel):
    """Tool metadata from TOOL_REGISTRY"""
    name: str
    description: str
    domain: str
    source: str
    source_priority: str
    providers: List[str] = Field(default_factory=list)
    return_fields: List[str] = Field(default_factory=list)


class ProviderStatus(BaseModel):
    """Provider availability status"""
    name: str
    available: bool
    reason: str = ""


class HealthResult(BaseModel):
    """SSE probe result for a single tool x provider"""
    tool: str
    provider: str
    status: Literal["ok", "error", "timeout"]
    response_time_ms: float = 0.0
    error: Optional[str] = None
    record_count: int = 0


class InvokeRequest(BaseModel):
    """Request to invoke a tool"""
    params: Dict[str, Any] = Field(default_factory=dict)


class InvokeResponse(BaseModel):
    """Response from a tool invocation"""
    tool: str
    provider: str
    status: Literal["ok", "error"]
    response_time_ms: float = 0.0
    data: Any = None
    error: Optional[str] = None
