from typing import Optional
from pydantic import BaseModel


class ConversionPoint(BaseModel):
    """转化率趋势数据点"""
    date: str
    new_contacts: int
    won: int


class ChannelDistribution(BaseModel):
    """渠道分布"""
    channel: str
    count: int
    percentage: float


class SalesRanking(BaseModel):
    """销售排名"""
    user_id: str
    user_name: str
    deal_count: int
    deal_amount: float
    conversion_rate: float


class AnalyticsOverview(BaseModel):
    """分析概览"""
    total_contacts: int
    total_won: int
    total_lost: int
    overall_conversion_rate: float
    total_deal_amount: float
    avg_deal_value: float


class AnalyticsDashboard(BaseModel):
    """完整分析报表"""
    overview: AnalyticsOverview
    conversion_trend: list[ConversionPoint]
    channel_distribution: list[ChannelDistribution]
    sales_ranking: list[SalesRanking]
