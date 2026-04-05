from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RequestLog(BaseModel):
    method: str
    path: str
    user_id: Optional[str] = None
    target_service: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    error: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LogStatistics(BaseModel):
    total_requests: int
    success_count: int
    error_count: int
    avg_response_time_ms: float
    requests_per_service: dict
