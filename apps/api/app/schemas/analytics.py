from datetime import datetime

from pydantic import BaseModel


class LeadItem(BaseModel):
    id: str
    category: str
    title: str
    value: str
    unit: str
    description: str
    icon: str
    order: int
    details: list[dict[str, str]] = []


class LeadCategory(BaseModel):
    id: str
    name: str
    icon: str
    leads: list[LeadItem]


class AnalyticsResponse(BaseModel):
    categories: list[LeadCategory]
    generated_at: datetime
    total_leads: int
