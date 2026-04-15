from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, field_validator


class ContactCreate(BaseModel):
    name: str
    company: Optional[str] = None
    industry: Optional[str] = None
    status: str = "lead"
    priority: str = "mid"
    deal_value: Decimal = Decimal("0.00")
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name is required")
        return v.strip()

    @field_validator("deal_value")
    @classmethod
    def deal_value_positive(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Deal value must be positive")
        return v


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deal_value: Optional[Decimal] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactResponse(BaseModel):
    id: str
    name: str
    company: Optional[str] = None
    industry: Optional[str] = None
    status: str
    priority: str
    deal_value: Decimal
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    last_contact: Optional[date] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedContacts(BaseModel):
    data: List[ContactResponse]
    total: int
    page: int
    page_size: int


class ImportError_(BaseModel):
    row: int
    field: str
    message: str


class ImportResult(BaseModel):
    total: int
    inserted: int
    updated: int
    skipped: int
    errors: List[ImportError_]
