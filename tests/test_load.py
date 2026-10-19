"""Tests for loading and validating the station table."""

import hashlib
import math
from pathlib import Path

import pandas as pd
import pytest

from moldova_drought.checksums import ChecksumError
from moldova_drought.load import (
    DataValidationError,
    load_stations,
    read_stations,
    station_points,
    validate_stations,
)


def make_stations() -> pd.DataFrame:
    """A small valid table: 2 stations x 6 months, SPEI-3 missing in each first 2 months."""
    dates = pd.date_range("2000-01-01", periods=6, freq="MS")
    rows = [
        {
            "station": name,
            "date": date,
            "spei_3": math.nan if i < 2 else 0.5,
            "station_lat": lat,
            "station_lon": 28.5,
        }
        for name, lat in [("North", 48.0), ("South", 46.0)]
        for i, date in enumerate(dates)
    ]
    return pd.DataFrame(rows)


def test_valid_table_passes() -> None:
    validate_stations(make_stations())


def test_row_order_does_not_matter() -> None:
    validate_stations(make_stations().sample(frac=1, random_state=0))


def test_duplicate_rows_fail() -> None:
    df = make_stations()
    df = pd.concat([df, df.iloc[[3]]], ignore_index=True)

    with pytest.raises(DataValidationError, match="duplicate"):
        validate_stations(df)


def test_missing_month_fails() -> None:
    df = make_stations().drop(index=4)

    with pytest.raises(DataValidationError, match="expected 12 rows"):
        validate_stations(df)


def test_station_with_two_locations_fails() -> None:
    df = make_stations()
    df.loc[3, "station_lat"] = 47.5

    with pytest.raises(DataValidationError, match="more than one coordinate"):
        validate_stations(df)


def test_swapped_lat_lon_fails() -> None:
    df = make_stations().rename(
        columns={"station_lat": "station_lon", "station_lon": "station_lat"}
    )

    with pytest.raises(DataValidationError, match="outside Moldova"):
        validate_stations(df)


def test_fill_value_fails() -> None:
    df = make_stations()
    df.loc[3, "spei_3"] = -99.0

    with pytest.raises(DataValidationError, match="beyond"):
        validate_stations(df)


def test_unexpected_missing_spei_fails() -> None:
    df = make_stations()
    df.loc[3, "spei_3"] = math.nan

    with pytest.raises(DataValidationError, match="missing in exactly"):
        validate_stations(df)


def test_read_keeps_needed_columns_and_builds_date(tmp_path: Path) -> None:
    csv = tmp_path / "stations.csv"
    csv.write_text(
        "station,year,month,spei_3,station_lat,station_lon,drought_class_7\n"
        "North,2000,2,0.1,48.0,28.5,Normal\n"
        "North,2000,1,,48.0,28.5,Extremely Wet\n"
    )

    df = read_stations(csv, hashlib.sha256(csv.read_bytes()).hexdigest())

    assert list(df.columns) == ["station", "spei_3", "station_lat", "station_lon", "date"]
    assert df["date"].tolist() == [pd.Timestamp("2000-01-01"), pd.Timestamp("2000-02-01")]


def test_read_rejects_wrong_checksum(tmp_path: Path) -> None:
    csv = tmp_path / "stations.csv"
    csv.write_text("station,year,month,spei_3,station_lat,station_lon\n")

    with pytest.raises(ChecksumError):
        read_stations(csv, "0" * 64)


def test_station_points_put_longitude_on_x() -> None:
    points = station_points(make_stations())

    assert list(points["station"]) == ["North", "South"]
    assert points.geometry.x.tolist() == [28.5, 28.5]
    assert points.geometry.y.tolist() == [48.0, 46.0]
    assert points.crs == "EPSG:4326"


def test_real_station_data_is_valid() -> None:
    df = load_stations()

    assert df["station"].nunique() == 16
    assert len(df) == 16 * 60 * 12
