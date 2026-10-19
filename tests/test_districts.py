"""Tests for district loading and station assignment."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

from moldova_drought import config
from moldova_drought.districts import assign_stations, district_months, load_districts
from moldova_drought.load import load_stations, station_points


def make_districts() -> gpd.GeoDataFrame:
    """Three side-by-side 0.5 x 0.5 degree squares in central Moldova."""
    return gpd.GeoDataFrame(
        {"district_id": ["MD-W", "MD-E", "MD-X"], "district": ["West", "East", "Empty"]},
        geometry=[
            box(28.0, 47.0, 28.5, 47.5),
            box(28.5, 47.0, 29.0, 47.5),
            box(29.0, 47.0, 29.5, 47.5),
        ],
        crs="EPSG:4326",
    )


def make_station_points() -> gpd.GeoDataFrame:
    """'Corner' sits in West's far corner; 'Edge' is in East, just across West's border."""
    return gpd.GeoDataFrame(
        {"station": ["Corner", "Edge"]},
        geometry=[Point(28.02, 47.02), Point(28.52, 47.25)],
        crs="EPSG:4326",
    )


def test_station_inside_beats_a_closer_neighbour() -> None:
    assignment = assign_stations(make_districts(), make_station_points()).set_index("district")

    assert assignment.loc["West", "station"] == "Corner"
    assert assignment.loc["West", "station_inside"]


def test_district_without_station_takes_the_nearest() -> None:
    assignment = assign_stations(make_districts(), make_station_points()).set_index("district")

    assert assignment.loc["Empty", "station"] == "Edge"
    assert not assignment.loc["Empty", "station_inside"]
    # From Empty's centre (29.25 E) to Edge (28.52 E) along 47.25 N: about 55 km.
    assert assignment.loc["Empty", "distance_km"] == pytest.approx(55.2, abs=0.5)


def test_district_months_has_one_row_per_district_per_month() -> None:
    assignment = pd.DataFrame({"district_id": ["MD-A", "MD-B"], "station": ["S1", "S1"]})
    monthly = pd.DataFrame(
        {
            "station": ["S1", "S1", "S1"],
            "date": pd.date_range("2000-01-01", periods=3, freq="MS"),
            "spei_3": [0.1, 0.2, 0.3],
        }
    )

    table = district_months(assignment, monthly)

    assert len(table) == 2 * 3
    assert table.loc[table["district_id"] == "MD-B", "spei_3"].tolist() == [0.1, 0.2, 0.3]


needs_boundaries = pytest.mark.skipif(
    not config.BOUNDARIES_GEOJSON.exists(),
    reason="boundaries not downloaded: run python -m moldova_drought.download",
)


@needs_boundaries
def test_real_districts_load_cleanly() -> None:
    districts = load_districts()

    assert len(districts) == 37
    assert "Singerei" in districts["district"].tolist()


@needs_boundaries
def test_real_assignment_covers_every_district() -> None:
    assignment = assign_stations(load_districts(), station_points(load_stations()))

    assert assignment["district_id"].is_unique
    assert len(assignment) == 37
    floresti = assignment.set_index("district").loc["Floresti"]
    assert floresti["station"] == "Camenca"  # its own station, though Balti is closer
