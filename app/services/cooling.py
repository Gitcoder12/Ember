"""Newton's law of cooling for packaged food.

    T(t) = T_ambient + (T_initial - T_ambient) * 2^(-t / half_life)

DEFAULT constants below are ASSUMED engineering estimates, not measurements. Replace them with
values fitted from real probe data via `python -m app.ml.calibrate` (see docs/).
"""

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

# Minutes for the food-to-ambient temperature gap to halve, by packaging (ASSUMED).
DEFAULT_PACKAGING_HALF_LIFE_MIN: Final[dict[str, float]] = {
    "insulated": 70.0,
    "foil": 50.0,
    "standard": 40.0,
    "unknown": 40.0,
    "paper": 30.0,
    "open_box": 25.0,
}

# Dense, liquid-rich food holds heat longer; thin, high-surface-area food loses it faster (ASSUMED).
DEFAULT_CATEGORY_FACTOR: Final[dict[str, float]] = {
    "biryani": 1.2,
    "curry": 1.2,
    "soup": 1.3,
    "dal": 1.2,
    "noodles": 0.9,
    "burger": 0.75,
    "pizza": 0.7,
    "fries": 0.6,
    "dosa": 0.7,
}
UNKNOWN_CATEGORY_FACTOR: Final[float] = 1.0


@dataclass(frozen=True)
class CoolingParameters:
    """Half-lives and food factors; `temp_uncertainty_c` is set only by calibration."""

    packaging_half_life_min: Mapping[str, float]
    category_factor: Mapping[str, float]
    temp_uncertainty_c: float | None = None

    def packaging_half_life(self, packaging_type: str) -> float:
        return self.packaging_half_life_min.get(
            packaging_type, self.packaging_half_life_min["unknown"]
        )

    def half_life_min(self, packaging_type: str, food_category: str) -> float:
        factor = self.category_factor.get(food_category, UNKNOWN_CATEGORY_FACTOR)
        return self.packaging_half_life(packaging_type) * factor


DEFAULT_PARAMETERS: Final = CoolingParameters(
    packaging_half_life_min=DEFAULT_PACKAGING_HALF_LIFE_MIN,
    category_factor=DEFAULT_CATEGORY_FACTOR,
)


def _positive_floats(raw: object, field: str) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{field} must be an object")
    cleaned: dict[str, float] = {}
    for key, value in raw.items():
        valid = isinstance(value, int | float) and not isinstance(value, bool)
        if not isinstance(key, str) or not valid or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{field}[{key!r}] must be a positive finite number")
        cleaned[key] = float(value)
    return cleaned


def parameters_from_dict(raw: Mapping[str, Any]) -> CoolingParameters:
    """Build parameters from calibration JSON. Missing entries fall back to the defaults."""
    sigma = raw.get("temp_uncertainty_c")
    if sigma is not None:
        sigma = _positive_floats({"temp_uncertainty_c": sigma}, "calibration")["temp_uncertainty_c"]
    return CoolingParameters(
        packaging_half_life_min={
            **DEFAULT_PACKAGING_HALF_LIFE_MIN,
            **_positive_floats(raw.get("packaging_half_life_min", {}), "packaging_half_life_min"),
        },
        category_factor={
            **DEFAULT_CATEGORY_FACTOR,
            **_positive_floats(raw.get("category_factor", {}), "category_factor"),
        },
        temp_uncertainty_c=sigma,
    )


def load_parameters(path: Path) -> CoolingParameters:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read calibration file {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"calibration file {path} must contain a JSON object")
    return parameters_from_dict(raw)


def cooled_temperature_c(
    *, initial_c: float, ambient_c: float, minutes: float, half_life_min: float
) -> float:
    values = {
        "initial_c": initial_c,
        "ambient_c": ambient_c,
        "minutes": minutes,
        "half_life_min": half_life_min,
    }
    if any(isinstance(value, bool) or not math.isfinite(value) for value in values.values()):
        raise ValueError("temperatures, minutes, and half_life_min must be finite")
    if minutes < 0:
        raise ValueError("minutes must be non-negative")
    if half_life_min <= 0:
        raise ValueError("half_life_min must be positive")
    return float(ambient_c + (initial_c - ambient_c) * 0.5 ** (minutes / half_life_min))


def arrival_temperature_c(
    *,
    packaging_type: str,
    food_category: str,
    ambient_c: float,
    exposure_minutes: float,
    initial_temp_c: float,
    parameters: CoolingParameters = DEFAULT_PARAMETERS,
) -> float:
    """Predicted food temperature after `exposure_minutes` outside the kitchen."""
    if exposure_minutes < 0:
        raise ValueError("exposure_minutes must be non-negative")
    return cooled_temperature_c(
        initial_c=initial_temp_c,
        ambient_c=ambient_c,
        minutes=exposure_minutes,
        half_life_min=parameters.half_life_min(packaging_type, food_category),
    )


def probability_below(threshold_c: float, mean_c: float, sigma_c: float) -> float:
    """P(actual temperature < threshold) when actual ~ Normal(mean, sigma).

    Sigma models our ignorance about real packaging, food volume and handling, which is why the
    output is a probability rather than a hard hot/cold call. Calibration replaces the assumed
    sigma with the measured prediction error.
    """
    values = {"threshold_c": threshold_c, "mean_c": mean_c, "sigma_c": sigma_c}
    if any(isinstance(value, bool) or not math.isfinite(value) for value in values.values()):
        raise ValueError("threshold_c, mean_c, and sigma_c must be finite")
    if sigma_c <= 0:
        raise ValueError("sigma_c must be positive")
    z_score = (threshold_c - mean_c) / sigma_c
    return 0.5 * (1.0 + math.erf(z_score / math.sqrt(2.0)))
