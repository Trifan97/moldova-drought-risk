"""Tests for the CARTO export: build both layers, write them, read them back."""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from moldova_drought.classify import classify_spei
from moldova_drought.export import monthly_layer, risk_layer, write_outputs


def make_districts() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"district_id": ["MD-A", "MD-B"], "district": ["A", "B"]},
        geometry=[box(28.0, 47.0, 28.5, 47.5), box(28.5, 47.0, 29.0, 47.5)],
        crs="EPSG:4326",
    )


def make_table() -> pd.DataFrame:
    """Two districts x two months."""
    spei = pd.Series([-1.2, 0.3, -1.2, 0.3])
    months = pd.DataFrame(
        {
            "district_id": ["MD-A", "MD-A", "MD-B", "MD-B"],
            "district": ["A", "A", "B", "B"],
            "date": pd.to_datetime(["2000-01-01", "2000-02-01"] * 2),
            "spei_3": spei,
        }
    )
    return months.join(classify_spei(spei))


def test_risk_layer_keeps_every_district() -> None:
    assignment = pd.DataFrame({"district_id": ["MD-A", "MD-B"], "district": ["A", "B"]})
    summary = pd.DataFrame({"district_id": ["MD-A"], "drought_change_pp": [2.5]})

    risk = risk_layer(make_districts(), assignment, summary)

    assert risk["district_id"].tolist() == ["MD-A", "MD-B"]
    assert risk["drought_change_pp"].isna().tolist() == [False, True]


def test_monthly_points_lie_inside_their_district() -> None:
    districts = make_districts()

    monthly = monthly_layer(districts, make_table())

    polygons = districts.set_index("district_id").geometry
    for district_id, point in zip(monthly["district_id"], monthly.geometry, strict=True):
        assert point.within(polygons[district_id])


def test_files_round_trip(tmp_path: Path) -> None:
    districts = make_districts()
    assignment = pd.DataFrame({"district_id": ["MD-A", "MD-B"], "district": ["A", "B"]})
    summary = pd.DataFrame({"district_id": ["MD-A", "MD-B"], "drought_change_pp": [2.5, -1.0]})
    risk = risk_layer(districts, assignment, summary)

    risk_path, monthly_path = write_outputs(risk, monthly_layer(districts, make_table()), tmp_path)

    risk_back = gpd.read_parquet(risk_path)
    monthly_back = gpd.read_parquet(monthly_path)
    assert set(risk_back.geom_type) == {"Polygon"}
    assert set(monthly_back.geom_type) == {"Point"}
    assert risk_back.crs == monthly_back.crs == "EPSG:4326"
    assert monthly_back["severity"].tolist() == ["Moderately dry", "Normal"] * 2
