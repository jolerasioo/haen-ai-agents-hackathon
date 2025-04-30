from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class LogSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    USER_ACTION = "USER_ACTION"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    SECURITY = "SECURITY"
    AGENT_ACTION = "AGENT_ACTION"
    INTEGRATION = "INTEGRATION"


class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: LogCategory
    severity: LogSeverity = LogSeverity.INFO
    source: str
    action: str
    description: str
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    tags: Optional[List[str]] = None


class LogQueryParams(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    category: Optional[LogCategory] = None
    severity: Optional[LogSeverity] = None
    source: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    search_text: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0


class LogResponse(BaseModel):
    logs: List[AuditLog]
    total_count: int
    next_offset: Optional[int] = None