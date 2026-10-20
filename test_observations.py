from pathlib import Path

import pytest

from app.ml.observations import (
    CSV_COLUMNS,
    Observation,
    parse_row,
    read_observations,
    write_observations,
)

GOOD_ROW = {
    "packaging_type": "Standard",
    "food_category": "Fried Rice",
    "ambient_c": "30",
    "initial_temp_c": "72",
    "exposure_minutes": "35",
    "measured_temp_c": "55",
}


def test_valid_row_is_parsed_and_labels_normalised() -> None:
    row = parse_row(GOOD_ROW)
    assert row.packaging_type == "standard"
    assert row.food_category == "fried_rice"
    assert row.measured_temp_c == 55.0


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"ambient_c": "abc"}, "non_numeric"),
        ({"ambient_c": ""}, "non_numeric"),
        ({"measured_temp_c": "nan"}, "non_finite"),
        ({"exposure_minutes": "0"}, "exposure_out_of_range"),
        ({"exposure_minutes": "9999"}, "exposure_out_of_range"),
        ({"initial_temp_c": "500"}, "temperature_out_of_range"),
        ({"initial_temp_c": "32"}, "no_cooling_signal"),
        ({"measured_temp_c": "90"}, "measurement_implausible"),
        ({"measured_temp_c": "10"}, "measurement_implausible"),
        ({"packaging_type": "  "}, "missing_label"),
    ],
)
def test_bad_rows_are_rejected_with_reason(override: dict[str, str], reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        parse_row({**GOOD_ROW, **override})


def test_csv_round_trip_and_rejection_counts(tmp_path: Path) -> None:
    path = tmp_path / "m.csv"
    write_observations(path, [Observation("paper", "soup", 25.0, 70.0, 30.0, 50.0)])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("paper,soup,25,70,30,not_a_number\n")
    result = read_observations(path)
    assert len(result.observations) == 1
    assert result.rejected == {"non_numeric": 1}


def test_missing_columns_raise(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("packaging_type,food_category\nfoil,soup\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        read_observations(path)


def test_csv_header_matches_schema(tmp_path: Path) -> None:
    path = tmp_path / "m.csv"
    write_observations(path, [])
    assert path.read_text(encoding="utf-8").strip().split(",") == list(CSV_COLUMNS)
