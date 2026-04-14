from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: str
    contact_id: Optional[str] = None
    channel: str
    direction: str
    sender_id: str
    recipient_id: str
    subject: Optional[str] = None
    body: str
    external_id: Optional[str] = None
    is_read: bool
    assigned_to: Optional[str] = None
    created_at: datetime
    contact_name: Optional[str] = None

    model_config = {"from_attributes": True}


class WhatsAppSendRequest(BaseModel):
    contact_id: str
    message: str


class EmailSendRequest(BaseModel):
    contact_id: str
    subject: str
    body: str


class PaginatedMessages(BaseModel):
    data: list[MessageResponse]
    total: int
    page: int
    page_size: int
