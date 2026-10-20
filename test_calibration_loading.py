import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.models.schemas import HeatRiskRequest
from app.services.cooling import (
    DEFAULT_PARAMETERS,
    CoolingParameters,
    load_parameters,
    parameters_from_dict,
)
from app.services.heat_prediction import predict_heat_risk, resolve_parameters

REQUEST = HeatRiskRequest.model_validate(
    {
        "restaurant_id": "rest_1",
        "food_category": "biryani",
        "distance_km": 5,
        "estimated_delivery_minutes": 30,
        "pickup_delay_minutes": 5,
        "packaging_type": "standard",
        "ambient_temperature_c": 30,
    }
)


def test_partial_calibration_merges_with_defaults() -> None:
    params = parameters_from_dict({"packaging_half_life_min": {"standard": 90}})
    assert params.packaging_half_life("standard") == 90.0
    assert params.packaging_half_life("paper") == DEFAULT_PARAMETERS.packaging_half_life("paper")
    assert params.temp_uncertainty_c is None


@pytest.mark.parametrize(
    "raw",
    [
        {"packaging_half_life_min": {"standard": -5}},
        {"packaging_half_life_min": {"standard": "fast"}},
        {"packaging_half_life_min": {"standard": True}},
        {"packaging_half_life_min": {"standard": float("inf")}},
        {"packaging_half_life_min": [1, 2]},
        {"category_factor": {"soup": 0}},
        {"temp_uncertainty_c": -1},
    ],
)
def test_invalid_calibration_is_rejected(raw: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        parameters_from_dict(raw)


def test_load_parameters_reports_bad_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot read"):
        load_parameters(tmp_path / "missing.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot read"):
        load_parameters(broken)
    wrong_shape = tmp_path / "list.json"
    wrong_shape.write_text("[1]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_parameters(wrong_shape)


def test_calibrated_half_life_changes_the_prediction() -> None:
    slow = CoolingParameters({**DEFAULT_PARAMETERS.packaging_half_life_min, "standard": 200.0}, {})
    default_result = predict_heat_risk(REQUEST, Settings(), DEFAULT_PARAMETERS)
    slow_result = predict_heat_risk(REQUEST, Settings(), slow)
    assert slow_result.predicted_arrival_temp_c > default_result.predicted_arrival_temp_c
    assert slow_result.heat_risk < default_result.heat_risk


def test_calibrated_uncertainty_overrides_assumed_sigma() -> None:
    tight = CoolingParameters(
        DEFAULT_PARAMETERS.packaging_half_life_min,
        DEFAULT_PARAMETERS.category_factor,
        temp_uncertainty_c=0.5,
    )
    slow_order = REQUEST.model_copy(update={"estimated_delivery_minutes": 60})
    loose = predict_heat_risk(slow_order, Settings(temp_uncertainty_c=15.0), DEFAULT_PARAMETERS)
    sharp = predict_heat_risk(slow_order, Settings(temp_uncertainty_c=15.0), tight)
    # Arrival is well below 57C: a tighter measured error band makes the cold call more certain.
    assert loose.predicted_arrival_temp_c < 57.0
    assert sharp.heat_risk > loose.heat_risk


def test_resolve_parameters_uses_configured_file(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps({"packaging_half_life_min": {"standard": 123}}), encoding="utf-8")
    assert (
        resolve_parameters(Settings(calibration_path=path)).packaging_half_life("standard") == 123.0
    )
    assert resolve_parameters(Settings()) is DEFAULT_PARAMETERS


def test_app_fails_fast_on_corrupt_calibration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import get_settings
    from app.main import create_app

    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    monkeypatch.setenv("EMBER_CALIBRATION_PATH", str(bad))
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="cannot read"):
            create_app()
    finally:
        monkeypatch.delenv("EMBER_CALIBRATION_PATH")
        get_settings.cache_clear()
    assert TestClient(create_app()).get("/health").status_code == 200
