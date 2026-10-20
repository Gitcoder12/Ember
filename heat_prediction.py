"""Heat-risk prediction: physics model -> probability -> action, with counterfactual explanation."""

from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from app.core.config import Settings, get_settings
from app.models.schemas import (
    ExpectedState,
    HeatRiskRequest,
    HeatRiskResponse,
    RecommendedAction,
    RiskFactor,
    RiskFactorName,
    RiskLevel,
)
from app.services.cooling import (
    DEFAULT_PARAMETERS,
    CoolingParameters,
    arrival_temperature_c,
    load_parameters,
    probability_below,
)

# "Fixed" values used to ask: how much risk would remain if this factor were healthy?
TARGET_DELIVERY_MINUTES = 20
NEUTRAL_AMBIENT_C = 25.0
BEST_PACKAGING = "insulated"
MIN_REPORTED_CONTRIBUTION = 0.01
HOT_MARGIN_C = 5.0  # arrival this far above the serving minimum still counts as "hot"


@dataclass(frozen=True)
class _Scenario:
    packaging_type: str
    food_category: str
    ambient_c: float
    pickup_delay_minutes: int
    delivery_minutes: int


@lru_cache(maxsize=8)
def _load_cached(path: str) -> CoolingParameters:
    return load_parameters(Path(path))


def resolve_parameters(settings: Settings) -> CoolingParameters:
    """Calibrated constants if configured (cached until restart), else the assumed defaults."""
    if settings.calibration_path is None:
        return DEFAULT_PARAMETERS
    return _load_cached(str(settings.calibration_path))


def _evaluate(
    scenario: _Scenario, settings: Settings, parameters: CoolingParameters
) -> tuple[float, float]:
    """Return (arrival temperature in C, probability it is below the serving minimum)."""
    arrival_c = arrival_temperature_c(
        packaging_type=scenario.packaging_type,
        food_category=scenario.food_category,
        ambient_c=scenario.ambient_c,
        exposure_minutes=scenario.pickup_delay_minutes + scenario.delivery_minutes,
        initial_temp_c=settings.initial_food_temp_c,
        parameters=parameters,
    )
    # A calibrated (measured) error band replaces the assumed one.
    sigma = parameters.temp_uncertainty_c or settings.temp_uncertainty_c
    risk = probability_below(settings.min_serving_temp_c, arrival_c, sigma)
    return arrival_c, risk


def _explain(
    scenario: _Scenario, baseline_risk: float, settings: Settings, parameters: CoolingParameters
) -> list[RiskFactor]:
    """Leave-one-out attribution: re-run the model with one factor fixed and measure the drop."""
    counterfactuals: dict[RiskFactorName, _Scenario] = {
        "pickup_delay": replace(scenario, pickup_delay_minutes=0),
        "delivery_duration": replace(
            scenario, delivery_minutes=min(scenario.delivery_minutes, TARGET_DELIVERY_MINUTES)
        ),
        "packaging": replace(scenario, packaging_type=BEST_PACKAGING),
        "cold_weather": replace(scenario, ambient_c=max(scenario.ambient_c, NEUTRAL_AMBIENT_C)),
    }
    factors = []
    for name, fixed in counterfactuals.items():
        _, fixed_risk = _evaluate(fixed, settings, parameters)
        contribution = round(baseline_risk - fixed_risk, 3)
        if contribution >= MIN_REPORTED_CONTRIBUTION:
            factors.append(RiskFactor(name=name, contribution=contribution))
    return sorted(factors, key=lambda factor: factor.contribution, reverse=True)


def _risk_level(risk: float, settings: Settings) -> RiskLevel:
    if risk >= settings.priority_risk_threshold:
        return "high"
    if risk >= settings.nudge_risk_threshold:
        return "medium"
    return "low"


_ACTION_BY_LEVEL: dict[RiskLevel, RecommendedAction] = {
    "low": "none",
    "medium": "nudge",
    "high": "priority_pickup",
}


def _expected_state(arrival_c: float, settings: Settings) -> ExpectedState:
    if arrival_c >= settings.min_serving_temp_c + HOT_MARGIN_C:
        return "hot"
    if arrival_c >= settings.min_serving_temp_c:
        return "warm"
    return "lukewarm_or_cold"


def predict_heat_risk(
    request: HeatRiskRequest,
    settings: Settings | None = None,
    parameters: CoolingParameters | None = None,
) -> HeatRiskResponse:
    config = settings or get_settings()
    physics = parameters or resolve_parameters(config)
    scenario = _Scenario(
        packaging_type=request.packaging_type,
        food_category=request.food_category,
        ambient_c=request.ambient_temperature_c,
        pickup_delay_minutes=request.pickup_delay_minutes,
        delivery_minutes=request.estimated_delivery_minutes,
    )
    arrival_c, risk = _evaluate(scenario, config, physics)
    factors = _explain(scenario, risk, config, physics)
    level = _risk_level(risk, config)
    return HeatRiskResponse(
        heat_risk=round(risk, 3),
        risk_level=level,
        expected_state=_expected_state(arrival_c, config),
        recommended_action=_ACTION_BY_LEVEL[level],
        predicted_arrival_temp_c=round(arrival_c, 1),
        primary_risk_factor=factors[0].name if factors else None,
        risk_factors=factors,
    )
