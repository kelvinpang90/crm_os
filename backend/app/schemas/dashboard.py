from pydantic import BaseModel
from typing import Optional


class KpiItem(BaseModel):
    key: str
    value: float
    change: Optional[float] = None


class FunnelStage(BaseModel):
    stage: str
    count: int
    amount: float


class AdminDashboardResponse(BaseModel):
    kpis: list[KpiItem]
    funnel: list[FunnelStage]


class ManagerDashboardResponse(BaseModel):
    kpis: list[KpiItem]
    funnel: list[FunnelStage]


class PipelineStage(BaseModel):
    stage: str
    count: int
    amount: float
    last_updated: Optional[str] = None


class SalesDashboardResponse(BaseModel):
    kpis: list[KpiItem]
    pipeline: list[PipelineStage]


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    user_name: str
    avatar_url: Optional[str] = None
    deal_amount: float
    deal_count: int
    win_rate: float


class LeaderboardResponse(BaseModel):
    month: str
    entries: list[LeaderboardEntry]


class GmvTrendPoint(BaseModel):
    label: str
    value: float


class GmvTrendResponse(BaseModel):
    period: str
    data: list[GmvTrendPoint]
