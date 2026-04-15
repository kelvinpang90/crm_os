from typing import Optional
from pydantic import BaseModel, field_validator


class SalesTargetCreate(BaseModel):
    user_id: str
    year: int
    month: int
    target_amount: float = 0
    target_count: int = 0

    @field_validator("month")
    @classmethod
    def valid_month(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError("Month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if v < 2020 or v > 2100:
            raise ValueError("Invalid year")
        return v


class SalesTargetUpdate(BaseModel):
    target_amount: Optional[float] = None
    target_count: Optional[int] = None


class SalesTargetResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    year: int
    month: int
    target_amount: float
    target_count: int
    created_at: str
    updated_at: str
