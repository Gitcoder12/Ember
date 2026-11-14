import pytest

from app.services.cooling import arrival_temperature_c, cooled_temperature_c, probability_below

BASE = {
    "packaging_type": "standard",
    "food_category": "biryani",
    "ambient_c": 30.0,
    "initial_temp_c": 75.0,
}


def test_zero_exposure_returns_initial_temperature() -> None:
    assert arrival_temperature_c(exposure_minutes=0, **BASE) == pytest.approx(75.0)


def test_temperature_decreases_monotonically_with_time() -> None:
    temps = [arrival_temperature_c(exposure_minutes=m, **BASE) for m in (0, 10, 30, 60, 120)]
    assert temps == sorted(temps, reverse=True)


def test_temperature_never_drops_below_ambient() -> None:
    assert arrival_temperature_c(exposure_minutes=10_000, **BASE) >= BASE["ambient_c"]


def test_better_packaging_retains_more_heat() -> None:
    temps = {
        packaging: arrival_temperature_c(
            **{**BASE, "packaging_type": packaging}, exposure_minutes=40
        )
        for packaging in ("insulated", "standard", "open_box")
    }
    assert temps["insulated"] > temps["standard"] > temps["open_box"]


def test_thin_food_cools_faster_than_dense_food() -> None:
    fries = arrival_temperature_c(**{**BASE, "food_category": "fries"}, exposure_minutes=30)
    soup = arrival_temperature_c(**{**BASE, "food_category": "soup"}, exposure_minutes=30)
    assert fries < soup


def test_unknown_inputs_fall_back_to_defaults() -> None:
    unknown = arrival_temperature_c(
        **{**BASE, "packaging_type": "mystery", "food_category": "mystery"}, exposure_minutes=30
    )
    standard = arrival_temperature_c(**{**BASE, "food_category": "mystery"}, exposure_minutes=30)
    assert unknown == pytest.approx(standard)


def test_negative_exposure_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        arrival_temperature_c(exposure_minutes=-1, **BASE)


def test_probability_is_half_at_threshold_and_bounded() -> None:
    assert probability_below(55, 55, 5) == pytest.approx(0.5)
    assert probability_below(55, 90, 5) < 0.001  # food far hotter than threshold
    assert probability_below(55, 20, 5) > 0.999  # food far colder than threshold


def test_probability_requires_positive_sigma() -> None:
    with pytest.raises(ValueError, match="positive"):
        probability_below(55, 55, 0)


def test_cooled_temperature_validates_inputs() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        cooled_temperature_c(initial_c=70, ambient_c=30, minutes=-1, half_life_min=40)
    with pytest.raises(ValueError, match="positive"):
        cooled_temperature_c(initial_c=70, ambient_c=30, minutes=10, half_life_min=0)


def test_one_half_life_halves_the_gap() -> None:
    temp = cooled_temperature_c(initial_c=70, ambient_c=30, minutes=40, half_life_min=40)
    assert temp == pytest.approx(50.0)


@pytest.mark.parametrize(
    ("ambient_c", "initial_c"),
    [(-30.0, 75.0), (55.0, 75.0)],
)
def test_extreme_supported_ambient_values_remain_between_initial_and_ambient(
    ambient_c: float, initial_c: float
) -> None:
    result = cooled_temperature_c(
        initial_c=initial_c, ambient_c=ambient_c, minutes=120, half_life_min=40
    )
    assert min(ambient_c, initial_c) <= result <= max(ambient_c, initial_c)


def test_near_zero_exposure_is_continuous_with_initial_temperature() -> None:
    result = arrival_temperature_c(exposure_minutes=1e-9, **BASE)
    assert result == pytest.approx(BASE["initial_temp_c"], abs=1e-8)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("initial_c", float("nan")),
        ("ambient_c", float("inf")),
        ("minutes", float("nan")),
        ("half_life_min", float("inf")),
    ],
)
def test_non_finite_cooling_inputs_are_rejected(field: str, value: float) -> None:
    inputs = {
        "initial_c": 70.0,
        "ambient_c": 30.0,
        "minutes": 10.0,
        "half_life_min": 40.0,
    }
    inputs[field] = value
    with pytest.raises(ValueError, match="finite"):
        cooled_temperature_c(**inputs)


@pytest.mark.parametrize(
    ("threshold", "mean", "sigma"),
    [
        (float("nan"), 55.0, 5.0),
        (55.0, float("inf"), 5.0),
        (55.0, 55.0, float("nan")),
    ],
)
def test_probability_rejects_non_finite_inputs(threshold: float, mean: float, sigma: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        probability_below(threshold, mean, sigma)
