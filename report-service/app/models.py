from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ReportCreate(BaseModel):
    report_type: str  # e.g. "traffic", "sales", "user_activity"
    title: str
    description: Optional[str] = None
    data: Optional[Any] = None


class ReportResponse(BaseModel):
    id: str
    report_type: str
    title: str
    description: Optional[str]
    data: Optional[Any]
    created_by: str
    created_at: datetime
