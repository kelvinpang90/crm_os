from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, field_validator


class TaskCreate(BaseModel):
    title: str
    contact_id: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "中"
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("任务标题不能为空")
        return v.strip()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    contact_id: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    contact_id: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str
    due_date: Optional[date] = None
    is_done: bool
    done_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    contact_name: Optional[str] = None
    assigned_to_name: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedTasks(BaseModel):
    data: list[TaskResponse]
    total: int
    page: int
    page_size: int
