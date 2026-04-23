from datetime import datetime
from typing import Any

from pydantic import BaseModel


class KPI(BaseModel):
    name: str
    value: float
    unit: str
    change: float
    trend: str


class DashboardData(BaseModel):
    kpis: list[KPI]
    charts: dict[str, Any]
    last_updated: datetime
