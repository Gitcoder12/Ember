"""API schemas. Validation here is the trust boundary: invalid input never reaches the model."""

from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Identifier = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_-]{1,64}$")
]
PackagingType = Literal["insulated", "foil", "standard", "paper", "open_box", "unknown"]
RiskLevel = Literal["low", "medium", "high"]
ExpectedState = Literal["hot", "warm", "lukewarm_or_cold"]
RecommendedAction = Literal["none", "nudge", "priority_pickup"]
RiskFactorName = Literal["pickup_delay", "delivery_duration", "packaging", "cold_weather"]
TemperatureRating = Literal["hot", "warm", "lukewarm", "cold"]
RefundDecision = Literal["refund_review", "no_action"]

# A courier cannot average faster than this; larger values mean the input is inconsistent.
MAX_PLAUSIBLE_SPEED_KMH = 100.0


class HeatRiskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    restaurant_id: Identifier
    food_category: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,49}$")
    distance_km: float = Field(ge=0, le=50, allow_inf_nan=False)
    estimated_delivery_minutes: int = Field(ge=0, le=240)
    pickup_delay_minutes: int = Field(ge=0, le=120)
    packaging_type: PackagingType
    ambient_temperature_c: float = Field(ge=-30, le=55, allow_inf_nan=False)

    @field_validator("food_category", "packaging_type", mode="before")
    @classmethod
    def _normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower().replace(" ", "_")
        return value

    @model_validator(mode="after")
    def _check_speed_is_physical(self) -> Self:
        if self.distance_km > 0 and self.estimated_delivery_minutes == 0:
            raise ValueError("positive distance requires positive delivery time")
        hours = max(self.estimated_delivery_minutes, 1) / 60
        if self.distance_km / hours > MAX_PLAUSIBLE_SPEED_KMH:
            raise ValueError("distance_km and estimated_delivery_minutes imply an impossible speed")
        return self


class RiskFactor(BaseModel):
    name: RiskFactorName
    contribution: float = Field(ge=0, le=1, description="Risk removed if this factor were fixed.")


class HeatRiskResponse(BaseModel):
    heat_risk: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    expected_state: ExpectedState
    recommended_action: RecommendedAction
    predicted_arrival_temp_c: float
    primary_risk_factor: RiskFactorName | None
    risk_factors: list[RiskFactor]


class RatingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: Identifier
    temperature_rating: TemperatureRating
    packaging_rating: int = Field(ge=1, le=5)
    predicted_heat_risk: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)


class RatingResponse(BaseModel):
    order_id: str
    temperature_rating: TemperatureRating
    refund_decision: RefundDecision
    model_corroborated: bool | None
