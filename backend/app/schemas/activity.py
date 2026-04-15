from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel


class ActivityCreate(BaseModel):
    type: Literal["phone", "email", "meeting", "WhatsApp", "other", "status change"]
    content: Optional[str] = None
    follow_date: Optional[datetime] = None


class ActivityResponse(BaseModel):
    id: str
    contact_id: str
    user_id: str
    user_name: Optional[str] = None
    type: str
    content: Optional[str] = None
    follow_date: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
