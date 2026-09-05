from typing import Literal

from pydantic import BaseModel, Field


class HeatRiskRequest(BaseModel):
    restaurant_id: str
    food_category: str
    distance_km: float = Field(ge=0)
    estimated_delivery_minutes: int = Field(ge=0)
    pickup_delay_minutes: int = Field(ge=0)
    packaging_type: str
    ambient_temperature_c: float


class HeatRiskResponse(BaseModel):
    heat_risk: float = Field(ge=0, le=1)
    risk_level: Literal["low", "medium", "high"]
    expected_state: Literal["hot", "warm", "lukewarm_or_cold"]
    recommended_action: Literal["none", "nudge", "priority_pickup", "refund_review"]


class RatingRequest(BaseModel):
    order_id: str
    temperature_rating: Literal["hot", "warm", "lukewarm", "cold"]
    packaging_rating: int = Field(ge=1, le=5)
