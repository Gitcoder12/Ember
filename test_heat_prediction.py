import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.models.schemas import HeatRiskRequest
from app.services.heat_prediction import predict_heat_risk

SETTINGS = Settings()


def make_request(**overrides: object) -> HeatRiskRequest:
    fields: dict[str, object] = {
        "restaurant_id": "rest_123",
        "food_category": "biryani",
        "distance_km": 5.0,
        "estimated_delivery_minutes": 30,
        "pickup_delay_minutes": 5,
        "packaging_type": "standard",
        "ambient_temperature_c": 30.0,
    }
    fields.update(overrides)
    return HeatRiskRequest.model_validate(fields)


def test_risk_increases_with_pickup_delay() -> None:
    risks = [
        predict_heat_risk(make_request(pickup_delay_minutes=delay), SETTINGS).heat_risk
        for delay in (0, 5, 15, 30)
    ]
    assert risks == sorted(risks)
    assert risks[-1] > risks[0]


def test_fast_insulated_order_is_low_risk_with_no_action() -> None:
    result = predict_heat_risk(
        make_request(
            packaging_type="insulated", estimated_delivery_minutes=15, pickup_delay_minutes=0
        ),
        SETTINGS,
    )
    assert result.risk_level == "low"
    assert result.recommended_action == "none"
    assert result.expected_state == "hot"
    assert result.primary_risk_factor is None


def test_slow_order_is_high_risk_and_prioritised() -> None:
    result = predict_heat_risk(
        make_request(
            packaging_type="paper", estimated_delivery_minutes=60, pickup_delay_minutes=25
        ),
        SETTINGS,
    )
    assert result.risk_level == "high"
    assert result.recommended_action == "priority_pickup"
    assert result.expected_state == "lukewarm_or_cold"


def test_primary_factor_identifies_pickup_delay() -> None:
    result = predict_heat_risk(
        make_request(
            packaging_type="insulated", estimated_delivery_minutes=18, pickup_delay_minutes=60
        ),
        SETTINGS,
    )
    assert result.primary_risk_factor == "pickup_delay"


def test_primary_factor_identifies_cold_weather() -> None:
    result = predict_heat_risk(
        make_request(
            packaging_type="insulated",
            estimated_delivery_minutes=20,
            pickup_delay_minutes=0,
            ambient_temperature_c=-20,
        ),
        Settings(min_serving_temp_c=60.0),
    )
    assert result.primary_risk_factor == "cold_weather"


def test_risk_factors_are_sorted_and_bounded() -> None:
    result = predict_heat_risk(
        make_request(
            packaging_type="paper", estimated_delivery_minutes=60, pickup_delay_minutes=20
        ),
        SETTINGS,
    )
    contributions = [factor.contribution for factor in result.risk_factors]
    assert contributions == sorted(contributions, reverse=True)
    assert all(0 < value <= result.heat_risk for value in contributions)


def test_input_text_is_normalised() -> None:
    request = make_request(food_category="  Fried Rice ", packaging_type="PAPER")
    assert request.food_category == "fried_rice"
    assert request.packaging_type == "paper"


@pytest.mark.parametrize(
    "overrides",
    [
        {"distance_km": -1},
        {"distance_km": 500},
        {"estimated_delivery_minutes": -5},
        {"pickup_delay_minutes": 10_000},
        {"ambient_temperature_c": -31},
        {"ambient_temperature_c": 56},
        {"ambient_temperature_c": float("nan")},
        {"ambient_temperature_c": 200},
        {"packaging_type": "wooden"},
        {"restaurant_id": "bad id; DROP TABLE"},
        {"food_category": ""},
        {"distance_km": 30, "estimated_delivery_minutes": 5},
    ],
)
def test_invalid_requests_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        make_request(**overrides)


def test_settings_reject_inconsistent_thresholds() -> None:
    with pytest.raises(ValidationError):
        Settings(nudge_risk_threshold=0.8, priority_risk_threshold=0.5)
    with pytest.raises(ValidationError):
        Settings(min_serving_temp_c=80.0, initial_food_temp_c=75.0)


def test_non_text_category_is_rejected_not_coerced() -> None:
    with pytest.raises(ValidationError):
        make_request(food_category=123)
