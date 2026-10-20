"""Measured-temperature observations: the ground truth that calibrates the physics model.

One observation = probe the food at packing/pickup (initial), probe again on arrival (measured),
and note the ambient temperature and the minutes between the two probes.
"""

import csv
import math
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

CSV_COLUMNS = (
    "packaging_type",
    "food_category",
    "ambient_c",
    "initial_temp_c",
    "exposure_minutes",
    "measured_temp_c",
)
MAX_EXPOSURE_MINUTES = 240.0
MIN_COOLING_SIGNAL_C = 5.0  # initial must exceed ambient by this much to carry any information
MEASUREMENT_MARGIN_C = 5.0  # slack for probe noise before a reading is called a gross error
TEMP_RANGE_C = (-30.0, 120.0)


@dataclass(frozen=True, slots=True)
class Observation:
    packaging_type: str
    food_category: str
    ambient_c: float
    initial_temp_c: float
    exposure_minutes: float
    measured_temp_c: float


@dataclass(frozen=True)
class ReadResult:
    observations: list[Observation]
    rejected: dict[str, int]


def _normalize_label(text: str | None) -> str:
    return (text or "").strip().lower().replace(" ", "_")


def parse_row(row: Mapping[str, str | None]) -> Observation:
    """Parse one CSV row. Raises ValueError whose message is the rejection reason."""
    try:
        ambient, initial, minutes, measured = (
            float(row[column] or "")
            for column in ("ambient_c", "initial_temp_c", "exposure_minutes", "measured_temp_c")
        )
    except ValueError as exc:
        raise ValueError("non_numeric") from exc
    if not all(math.isfinite(value) for value in (ambient, initial, minutes, measured)):
        raise ValueError("non_finite")
    if not 0 < minutes <= MAX_EXPOSURE_MINUTES:
        raise ValueError("exposure_out_of_range")
    low, high = TEMP_RANGE_C
    if not all(low <= value <= high for value in (ambient, initial, measured)):
        raise ValueError("temperature_out_of_range")
    if initial - ambient < MIN_COOLING_SIGNAL_C:
        raise ValueError("no_cooling_signal")
    if measured > initial + MEASUREMENT_MARGIN_C or measured < ambient - MEASUREMENT_MARGIN_C:
        raise ValueError("measurement_implausible")
    packaging = _normalize_label(row["packaging_type"])
    category = _normalize_label(row["food_category"])
    if not packaging or not category:
        raise ValueError("missing_label")
    return Observation(packaging, category, ambient, initial, minutes, measured)


def read_observations(path: Path) -> ReadResult:
    """Read and validate a CSV. Bad rows are counted by reason, never silently trusted."""
    observations: list[Observation] = []
    rejected: Counter[str] = Counter()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(CSV_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {sorted(missing)}")
        for row in reader:
            try:
                observations.append(parse_row(row))
            except ValueError as exc:
                rejected[str(exc)] += 1
    return ReadResult(observations, dict(rejected))


def write_observations(path: Path, observations: Iterable[Observation]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for item in observations:
            writer.writerow(
                [
                    item.packaging_type,
                    item.food_category,
                    round(item.ambient_c, 2),
                    round(item.initial_temp_c, 2),
                    round(item.exposure_minutes, 2),
                    round(item.measured_temp_c, 2),
                ]
            )
