"""Build the two CARTO tables and write them as GeoParquet."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from moldova_drought import config

RISK_FILE = "synthetic_district_drought_risk.parquet"
MONTHLY_FILE = "synthetic_district_monthly_spei.parquet"


def risk_layer(
    districts: gpd.GeoDataFrame, assignment: pd.DataFrame, summary: pd.DataFrame
) -> gpd.GeoDataFrame:
    """37 district polygons with their station and drought-risk summary."""
    # how="left" keeps all districts: a missing summary shows up as blanks, not a lost row.
    return districts.merge(
        assignment.drop(columns="district"), on="district_id", how="left", validate="one_to_one"
    ).merge(summary, on="district_id", how="left", validate="one_to_one")


def monthly_layer(districts: gpd.GeoDataFrame, table: pd.DataFrame) -> gpd.GeoDataFrame:
    """One point per district per month, placed at the district's interior point.

    Points rather than polygons: repeating each polygon for all 720 months would
    duplicate the same shapes, which CARTO advises against.
    """
    anchors = gpd.GeoDataFrame(
        districts[["district_id"]],
        geometry=districts.to_crs(config.MOLDOVA_CRS).representative_point(),
    ).to_crs(districts.crs)
    columns = ["district_id", "district", "date", "spei_3", "severity", "severity_code"]
    monthly = anchors.merge(table[columns], on="district_id", validate="one_to_many")
    # Plain strings, not a pandas categorical: the safest type for a data warehouse.
    monthly["severity"] = monthly["severity"].astype(str)
    return monthly[[*columns, "geometry"]]


def write_outputs(risk: gpd.GeoDataFrame, monthly: gpd.GeoDataFrame, out_dir: Path) -> list[Path]:
    """Write both tables to out_dir as GeoParquet and return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / RISK_FILE, out_dir / MONTHLY_FILE]
    for layer, path in zip([risk, monthly], paths, strict=True):
        layer.to_parquet(path, index=False)
    return paths
