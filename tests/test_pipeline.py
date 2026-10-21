"""End to end: the real inputs produce both CARTO tables."""

from pathlib import Path

import geopandas as gpd
import pytest

from moldova_drought import config
from moldova_drought.pipeline import run


@pytest.mark.skipif(
    not config.BOUNDARIES_GEOJSON.exists(),
    reason="boundaries not downloaded: run python -m moldova_drought.download",
)
def test_pipeline_writes_both_tables(tmp_path: Path) -> None:
    risk_path, monthly_path = run(tmp_path)

    risk = gpd.read_parquet(risk_path)
    monthly = gpd.read_parquet(monthly_path)
    assert len(risk) == 37
    assert risk["drought_pct_1961_1990"].between(0, 100).all()
    assert risk["drought_pct_1991_2020"].between(0, 100).all()
    assert risk["drought_change_pp"].notna().all()
    assert len(monthly) == 37 * 720
    assert (monthly["severity"] == "No data").sum() == 37 * 2
