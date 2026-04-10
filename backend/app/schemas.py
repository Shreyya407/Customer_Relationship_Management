from __future__ import annotations

from pydantic import BaseModel


class CustomerSummary(BaseModel):
    customer_id: int
    country: str
    orders: int
    items: int
    revenue: float
    last_purchase_days: int
    recency_score: int
    frequency_score: int
    monetary_score: int
    segment: str


class DashboardSummary(BaseModel):
    total_customers: int
    total_orders: int
    total_revenue: float
    average_order_value: float
    segment_counts: dict[str, int]
    top_customers: list[CustomerSummary]
