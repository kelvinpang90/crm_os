from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class RoutingRuleCreate(BaseModel):
    name: str
    strategy: str
    conditions: Optional[dict] = None
    target_users: list[str]
    priority: int = 0
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rule name is required")
        return v.strip()

    @field_validator("strategy")
    @classmethod
    def valid_strategy(cls, v: str) -> str:
        if v not in ("workload", "region", "win_rate"):
            raise ValueError("Invalid allocation strategy")
        return v


class RoutingRuleUpdate(BaseModel):
    name: Optional[str] = None
    strategy: Optional[str] = None
    conditions: Optional[dict] = None
    target_users: Optional[list[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class RoutingRuleResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    priority: int
    strategy: str
    conditions: Optional[dict] = None
    target_users: Optional[list[str]] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReorderItem(BaseModel):
    id: str
    priority: int


class ReorderRequest(BaseModel):
    rules: list[ReorderItem]
