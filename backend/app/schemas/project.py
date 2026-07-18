from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, field_validator

MIN_STEP = 1
MAX_STEP = 12


class ProjectCreate(BaseModel):
    customer_name: str
    address: str = ""
    service_type: str = ""
    project_manager: str = ""
    current_step: int = 1

    @field_validator("current_step")
    @classmethod
    def step_in_range(cls, v: int) -> int:
        if not (MIN_STEP <= v <= MAX_STEP):
            raise ValueError(f"current_step must be between {MIN_STEP} and {MAX_STEP}")
        return v


class ProjectUpdate(BaseModel):
    customer_name: Optional[str] = None
    address: Optional[str] = None
    service_type: Optional[str] = None
    project_manager: Optional[str] = None
    current_step: Optional[int] = None

    @field_validator("current_step")
    @classmethod
    def step_in_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (MIN_STEP <= v <= MAX_STEP):
            raise ValueError(f"current_step must be between {MIN_STEP} and {MAX_STEP}")
        return v


class ProjectAdvance(BaseModel):
    note: Optional[str] = None


class ProjectStepHistoryResponse(BaseModel):
    id: str
    project_id: str
    step_no: int
    entered_at: datetime
    updated_by: str
    note: Optional[str] = None
    photos: List[str] = []


class ProjectResponse(BaseModel):
    id: str
    customer_name: str
    address: str
    service_type: str
    project_manager: str
    current_step: int
    created_at: datetime
    last_updated_at: datetime
    history: List[ProjectStepHistoryResponse] = []
