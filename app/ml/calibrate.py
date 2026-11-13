"""Fit the cooling model to real measurements.

Why this instead of a black-box ML model: the physics already has the right shape, so only a few
numbers (half-lives) are unknown. Fitting them needs far less data than ML and stays explainable.
Fitting happens in TEMPERATURE space, so the residual error comes out in degrees Celsius, which is
exactly the uncertainty the risk probability needs.

Usage:  python -m app.ml.calibrate measurements.csv -o calibration.json
"""

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from app.ml.observations import Observation, read_observations
from app.services.cooling import DEFAULT_PARAMETERS, CoolingParameters, cooled_temperature_c

MIN_ROWS_TOTAL = 20
MIN_ROWS_PER_GROUP = 8
HALF_LIFE_BOUNDS = (2.0, 1000.0)
FACTOR_BOUNDS = (0.2, 5.0)
HOLDOUT_FRACTION = 0.2
MIN_HOLDOUT_ROWS = 5
DEFAULT_BOOTSTRAP_ROUNDS = 100
_INV_PHI = (math.sqrt(5.0) - 1.0) / 2.0


class CalibrationError(ValueError):
    """Raised when the data cannot support a calibration."""


@dataclass(frozen=True, slots=True)
class _Row:
    initial_gap_c: float
    ambient_c: float
    minutes: float
    measured_c: float
    multiplier: float  # the other (fixed) factor in half_life = scale * multiplier


@dataclass(frozen=True)
class GroupFit:
    name: str
    n: int
    value: float
    ci_low: float | None
    ci_high: float | None
    fitted: bool


@dataclass(frozen=True)
class CalibrationResult:
    parameters: CoolingParameters
    packaging: list[GroupFit]
    categories: list[GroupFit]
    rows_used: int
    rows_rejected: dict[str, int]
    rmse_c: float
    holdout_rmse_c: float | None
    baseline_rmse_c: float
    baseline_holdout_rmse_c: float | None

    def to_dict(self) -> dict[str, Any]:
        """JSON in the format `load_parameters` reads. Only fitted groups are written."""
        return {
            "packaging_half_life_min": {
                g.name: round(g.value, 2) for g in self.packaging if g.fitted
            },
            "category_factor": {g.name: round(g.value, 3) for g in self.categories if g.fitted},
            "temp_uncertainty_c": round(self.parameters.temp_uncertainty_c or 0.0, 2),
            "metadata": {
                "rows_used": self.rows_used,
                "rows_rejected": self.rows_rejected,
                "rmse_c": round(self.rmse_c, 2),
                "holdout_rmse_c": _round_or_none(self.holdout_rmse_c),
                "baseline_rmse_c": round(self.baseline_rmse_c, 2),
                "baseline_holdout_rmse_c": _round_or_none(self.baseline_holdout_rmse_c),
                "packaging_ci95": {
                    g.name: [round(g.ci_low, 2), round(g.ci_high, 2)]
                    for g in self.packaging
                    if g.fitted and g.ci_low is not None and g.ci_high is not None
                },
            },
        }


def _round_or_none(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def _sse(rows: Sequence[_Row], scale: float) -> float:
    total = 0.0
    for row in rows:
        predicted = row.ambient_c + row.initial_gap_c * 0.5 ** (
            row.minutes / (scale * row.multiplier)
        )
        total += (row.measured_c - predicted) ** 2
    return total


def _golden_minimize(objective: Callable[[float], float], bounds: tuple[float, float]) -> float:
    """Minimise a unimodal objective over log-space. No dependencies, no gradient needed."""
    low, high = math.log(bounds[0]), math.log(bounds[1])
    c = high - _INV_PHI * (high - low)
    d = low + _INV_PHI * (high - low)
    f_c, f_d = objective(math.exp(c)), objective(math.exp(d))
    for _ in range(50):
        if f_c < f_d:
            high, d, f_d = d, c, f_c
            c = high - _INV_PHI * (high - low)
            f_c = objective(math.exp(c))
        else:
            low, c, f_c = c, d, f_d
            d = low + _INV_PHI * (high - low)
            f_d = objective(math.exp(d))
    return math.exp((low + high) / 2.0)


def _fit_scale(rows: Sequence[_Row], bounds: tuple[float, float]) -> float:
    return _golden_minimize(lambda scale: _sse(rows, scale), bounds)


def _bootstrap_ci(
    rows: Sequence[_Row], bounds: tuple[float, float], rounds: int, rng: random.Random
) -> tuple[float | None, float | None]:
    if rounds <= 0:
        return None, None
    estimates = sorted(_fit_scale(rng.choices(rows, k=len(rows)), bounds) for _ in range(rounds))
    last = len(estimates) - 1
    return estimates[int(0.025 * last)], estimates[math.ceil(0.975 * last)]


def _group_by(
    observations: Sequence[Observation], key: Callable[[Observation], str]
) -> dict[str, list[Observation]]:
    groups: dict[str, list[Observation]] = defaultdict(list)
    for item in observations:
        groups[key(item)].append(item)
    return dict(groups)


def _fit_parameters(
    observations: Sequence[Observation],
    base: CoolingParameters,
    rounds: int,
    rng: random.Random,
) -> tuple[CoolingParameters, list[GroupFit], list[GroupFit]]:
    """Pass 1 fits packaging half-lives; pass 2 refines per-category factors on top of them."""
    packaging_values = dict(base.packaging_half_life_min)
    packaging_fits: list[GroupFit] = []
    for name, group in sorted(_group_by(observations, lambda o: o.packaging_type).items()):
        if len(group) < MIN_ROWS_PER_GROUP:
            packaging_fits.append(
                GroupFit(name, len(group), base.packaging_half_life(name), None, None, False)
            )
            continue
        rows = [
            _Row(
                o.initial_temp_c - o.ambient_c,
                o.ambient_c,
                o.exposure_minutes,
                o.measured_temp_c,
                base.category_factor.get(o.food_category, 1.0),
            )
            for o in group
        ]
        value = _fit_scale(rows, HALF_LIFE_BOUNDS)
        low, high = _bootstrap_ci(rows, HALF_LIFE_BOUNDS, rounds, rng)
        packaging_values[name] = value
        packaging_fits.append(GroupFit(name, len(group), value, low, high, True))

    after_packaging = CoolingParameters(packaging_values, base.category_factor)
    category_values = dict(base.category_factor)
    category_fits: list[GroupFit] = []
    for name, group in sorted(_group_by(observations, lambda o: o.food_category).items()):
        if len(group) < MIN_ROWS_PER_GROUP:
            category_fits.append(
                GroupFit(name, len(group), base.category_factor.get(name, 1.0), None, None, False)
            )
            continue
        rows = [
            _Row(
                o.initial_temp_c - o.ambient_c,
                o.ambient_c,
                o.exposure_minutes,
                o.measured_temp_c,
                after_packaging.packaging_half_life(o.packaging_type),
            )
            for o in group
        ]
        value = _fit_scale(rows, FACTOR_BOUNDS)
        low, high = _bootstrap_ci(rows, FACTOR_BOUNDS, rounds, rng)
        category_values[name] = value
        category_fits.append(GroupFit(name, len(group), value, low, high, True))
    return CoolingParameters(packaging_values, category_values), packaging_fits, category_fits


def _rmse(observations: Sequence[Observation], parameters: CoolingParameters) -> float:
    total = 0.0
    for o in observations:
        predicted = cooled_temperature_c(
            initial_c=o.initial_temp_c,
            ambient_c=o.ambient_c,
            minutes=o.exposure_minutes,
            half_life_min=parameters.half_life_min(o.packaging_type, o.food_category),
        )
        total += (o.measured_temp_c - predicted) ** 2
    return math.sqrt(total / len(observations))


def calibrate(
    observations: Sequence[Observation],
    *,
    seed: int = 0,
    bootstrap_rounds: int = DEFAULT_BOOTSTRAP_ROUNDS,
    base: CoolingParameters = DEFAULT_PARAMETERS,
    rows_rejected: dict[str, int] | None = None,
) -> CalibrationResult:
    if len(observations) < MIN_ROWS_TOTAL:
        raise CalibrationError(
            f"need at least {MIN_ROWS_TOTAL} valid rows, got {len(observations)}"
        )
    rng = random.Random(seed)
    shuffled = list(observations)
    rng.shuffle(shuffled)
    split = int(len(shuffled) * (1.0 - HOLDOUT_FRACTION))
    train, test = shuffled[:split], shuffled[split:]

    # Honest accuracy: fit on 80%, score on the unseen 20%, compare with the assumed defaults.
    holdout_rmse = baseline_holdout = None
    if len(test) >= MIN_HOLDOUT_ROWS:
        trained, _, _ = _fit_parameters(train, base, 0, rng)
        holdout_rmse, baseline_holdout = _rmse(test, trained), _rmse(test, base)

    fitted, packaging_fits, category_fits = _fit_parameters(
        observations, base, bootstrap_rounds, rng
    )
    n_params = sum(g.fitted for g in packaging_fits + category_fits)
    degrees_of_freedom = max(len(observations) - n_params, 1)
    in_sample = _rmse(observations, fitted) * math.sqrt(len(observations) / degrees_of_freedom)
    # Use the larger of in-sample and holdout error so the stated uncertainty is never optimistic.
    sigma = max(in_sample, holdout_rmse or 0.0)
    return CalibrationResult(
        parameters=replace(fitted, temp_uncertainty_c=sigma),
        packaging=packaging_fits,
        categories=category_fits,
        rows_used=len(observations),
        rows_rejected=rows_rejected or {},
        rmse_c=in_sample,
        holdout_rmse_c=holdout_rmse,
        baseline_rmse_c=_rmse(observations, base),
        baseline_holdout_rmse_c=baseline_holdout,
    )


def format_report(result: CalibrationResult) -> str:
    lines = [f"rows used: {result.rows_used}   rejected: {result.rows_rejected or 0}"]
    lines.append("packaging half-life (min) [95% CI]:")
    for fit in result.packaging:
        if fit.fitted and fit.ci_low is not None and fit.ci_high is not None:
            interval = f"[{fit.ci_low:.1f}, {fit.ci_high:.1f}]"
            lines.append(f"  {fit.name:<10} n={fit.n:<5} {fit.value:6.1f}  {interval}")
        else:
            state = "fitted" if fit.fitted else f"kept default (n<{MIN_ROWS_PER_GROUP})"
            lines.append(f"  {fit.name:<10} n={fit.n:<5} {fit.value:6.1f}  {state}")
    lines.append(
        f"error in-sample: {result.rmse_c:.2f} C   "
        f"(assumed defaults: {result.baseline_rmse_c:.2f} C)"
    )
    if result.holdout_rmse_c is not None and result.baseline_holdout_rmse_c is not None:
        lines.append(
            f"error on unseen 20%: {result.holdout_rmse_c:.2f} C   "
            f"(assumed defaults: {result.baseline_holdout_rmse_c:.2f} C)"
        )
    lines.append(f"temp_uncertainty_c written: {result.parameters.temp_uncertainty_c:.2f}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate Ember's cooling model from probe data.")
    parser.add_argument("measurements", type=Path, help="CSV of probe measurements")
    parser.add_argument("-o", "--output", type=Path, default=Path("calibration.json"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--bootstrap", type=int, default=DEFAULT_BOOTSTRAP_ROUNDS)
    args = parser.parse_args(argv)
    try:
        data = read_observations(args.measurements)
        result = calibrate(
            data.observations,
            seed=args.seed,
            bootstrap_rounds=args.bootstrap,
            rows_rejected=data.rejected,
        )
        args.output.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"calibration failed: {exc}", file=sys.stderr)
        return 2
    print(format_report(result))
    print(f"written: {args.output}  (set EMBER_CALIBRATION_PATH to use it)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
