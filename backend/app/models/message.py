import uuid
from datetime import datetime

from sqlalchemy import String, Enum, Text, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    contact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    channel: Mapped[str] = mapped_column(
        Enum("whatsapp", "email", name="message_channel"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Enum("inbound", "outbound", name="message_direction"), nullable=False
    )
    sender_id: Mapped[str] = mapped_column(String(200), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str | None] = mapped_column(
        String(200), unique=True, nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assigned_to: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_msg_contact_id", "contact_id"),
        Index("idx_msg_channel", "channel"),
        Index("idx_msg_sender_id", "sender_id"),
        Index("idx_msg_created_at", "created_at"),
    )
