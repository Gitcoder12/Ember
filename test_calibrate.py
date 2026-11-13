import json
from pathlib import Path

import pytest

from app.ml.calibrate import CalibrationError, calibrate, main
from app.ml.observations import write_observations
from app.ml.synthetic import TRUE_PARAMETERS, generate_observations
from app.services.cooling import DEFAULT_PARAMETERS, load_parameters

NOISE_SD_C = 2.0


@pytest.fixture(scope="module")
def synthetic_rows() -> list:
    return generate_observations(900, seed=7, noise_sd_c=NOISE_SD_C)


@pytest.fixture(scope="module")
def result(synthetic_rows: list):  # type: ignore[no-untyped-def]
    return calibrate(synthetic_rows, seed=1, bootstrap_rounds=40)


def test_recovers_true_packaging_half_lives(result) -> None:  # type: ignore[no-untyped-def]
    for fit in result.packaging:
        truth = TRUE_PARAMETERS.packaging_half_life(fit.name)
        assert fit.fitted
        assert fit.value == pytest.approx(truth, rel=0.10), fit.name


def test_error_matches_injected_noise(result) -> None:  # type: ignore[no-untyped-def]
    assert result.rmse_c == pytest.approx(NOISE_SD_C, abs=0.5)
    assert result.holdout_rmse_c is not None
    assert result.holdout_rmse_c == pytest.approx(NOISE_SD_C, abs=0.8)


def test_calibration_beats_assumed_defaults(result) -> None:  # type: ignore[no-untyped-def]
    assert result.rmse_c < result.baseline_rmse_c / 2
    assert result.baseline_holdout_rmse_c is not None
    assert result.holdout_rmse_c < result.baseline_holdout_rmse_c / 2


def test_confidence_intervals_bracket_the_estimate(result) -> None:  # type: ignore[no-untyped-def]
    for fit in result.packaging:
        assert fit.ci_low is not None and fit.ci_high is not None
        assert fit.ci_low <= fit.value <= fit.ci_high
        assert (fit.ci_high - fit.ci_low) / fit.value < 0.30


def test_reported_uncertainty_is_never_optimistic(result) -> None:  # type: ignore[no-untyped-def]
    sigma = result.parameters.temp_uncertainty_c
    assert sigma is not None
    assert sigma >= result.rmse_c
    assert sigma >= (result.holdout_rmse_c or 0.0)
    assert sigma >= 0.01


def test_calibration_is_deterministic(synthetic_rows: list) -> None:
    first = calibrate(synthetic_rows[:200], seed=3, bootstrap_rounds=10)
    second = calibrate(synthetic_rows[:200], seed=3, bootstrap_rounds=10)
    assert first.to_dict() == second.to_dict()


def test_sparse_groups_keep_defaults() -> None:
    rows = generate_observations(60, seed=2)
    rare = [r for r in rows if r.packaging_type == "foil"][:3]
    others = [r for r in rows if r.packaging_type != "foil"]
    outcome = calibrate(others + rare, bootstrap_rounds=0)
    foil = next(fit for fit in outcome.packaging if fit.name == "foil")
    assert not foil.fitted
    assert foil.value == DEFAULT_PARAMETERS.packaging_half_life("foil")
    assert "foil" not in outcome.to_dict()["packaging_half_life_min"]


def test_too_few_rows_raises() -> None:
    with pytest.raises(CalibrationError, match="at least"):
        calibrate(generate_observations(5, seed=1))


def test_json_output_round_trips_into_parameters(result, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps(result.to_dict()), encoding="utf-8")
    loaded = load_parameters(path)
    assert loaded.temp_uncertainty_c == pytest.approx(
        result.parameters.temp_uncertainty_c, abs=0.01
    )
    assert loaded.packaging_half_life("standard") == pytest.approx(
        result.parameters.packaging_half_life("standard"), abs=0.01
    )


def test_cli_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_path, out_path = tmp_path / "m.csv", tmp_path / "calibration.json"
    write_observations(csv_path, generate_observations(150, seed=5))
    assert main([str(csv_path), "-o", str(out_path), "--bootstrap", "5"]) == 0
    assert "error on unseen 20%" in capsys.readouterr().out
    assert load_parameters(out_path).temp_uncertainty_c is not None


def test_cli_reports_failures_with_exit_code_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(tmp_path / "missing.csv")]) == 2
    assert "calibration failed" in capsys.readouterr().err
    tiny = tmp_path / "tiny.csv"
    write_observations(tiny, generate_observations(5, seed=1))
    assert main([str(tiny), "-o", str(tmp_path / "x.json")]) == 2


def test_synthetic_generator_validates_inputs() -> None:
    with pytest.raises(ValueError, match="positive"):
        generate_observations(0, seed=1)
    with pytest.raises(ValueError, match="non-negative"):
        generate_observations(5, seed=1, noise_sd_c=-1)



def test_near_zero_fit_uncertainty_remains_loadable(tmp_path: Path) -> None:
    rows = generate_observations(120, seed=12, noise_sd_c=0.0)
    result = calibrate(rows, seed=4, bootstrap_rounds=0)
    payload = result.to_dict()

    assert payload["temp_uncertainty_c"] >= 0.01
    path = tmp_path / "near-perfect-calibration.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_parameters(path).temp_uncertainty_c >= 0.01
