from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class QueryType(str, Enum):
    METRICS = "metrics"
    ALERTS = "alerts"
    LOGS = "logs"
    GENERAL = "general"
    HEALTH = "health"

class ChatMessage(BaseModel):
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class MetricData(BaseModel):
    metric_name: str
    values: List[Dict[str, Any]]
    labels: Dict[str, str] = Field(default_factory=dict)
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    unit: Optional[str] = None
    description: Optional[str] = None

class AlertData(BaseModel):
    alert_name: str
    severity: str
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str] = Field(default_factory=dict)
    active_at: datetime
    value: Optional[float] = None
    fingerprint: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    message_type: MessageType = MessageType.ASSISTANT
    session_id: str
    query_type: Optional[QueryType] = None
    data: Optional[Dict[str, Any]] = None
    metrics: Optional[List[MetricData]] = None
    alerts: Optional[List[AlertData]] = None
    suggestions: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None
    confidence: Optional[float] = None

class HealthCheck(BaseModel):
    service: str
    status: str  # healthy, unhealthy, degraded
    message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str  # healthy, unhealthy, degraded
    timestamp: datetime
    checks: Dict[str, Any]
    version: str
    uptime: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    context: Optional[Dict[str, Any]] = None

class MetricsSummary(BaseModel):
    total_metrics: int
    services: List[str]
    namespaces: List[str]
    last_updated: datetime
    health_score: Optional[float] = None