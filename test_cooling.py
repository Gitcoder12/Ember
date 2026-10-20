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
