"""Districts: load the boundaries and give each district one station's SPEI series."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from moldova_drought import config
from moldova_drought.checksums import verify_sha256
from moldova_drought.load import DataValidationError


def load_districts(
    path: Path = config.BOUNDARIES_GEOJSON, expected_sha256: str = config.BOUNDARIES_SHA256
) -> gpd.GeoDataFrame:
    """Read the district boundaries: ISO 3166-2 code, name and geometry."""
    verify_sha256(path, expected_sha256)
    districts = gpd.read_file(path).rename(
        columns={"shapeISO": "district_id", "shapeName": "district"}
    )
    # The source dropped diacritics but kept some capitals: "SIngerei" -> "Singerei".
    districts["district"] = districts["district"].str.title()
    if not districts["district_id"].is_unique:
        raise DataValidationError("district_id (ISO code) is not unique")
    return districts[["district_id", "district", "geometry"]].sort_values(
        "district_id", ignore_index=True
    )


def assign_stations(districts: gpd.GeoDataFrame, stations: gpd.GeoDataFrame) -> pd.DataFrame:
    """Pick one station per district.

    A station inside the district wins; otherwise the nearest station is used. Among
    equals, the station closest to the district's interior point wins. distance_km is
    measured from that interior point, in Moldova's metric CRS.
    """
    districts_m = districts.to_crs(config.MOLDOVA_CRS)
    stations_m = stations.to_crs(config.MOLDOVA_CRS)

    rows = []
    for district_id, district, polygon in zip(
        districts_m["district_id"], districts_m["district"], districts_m.geometry, strict=True
    ):
        # representative_point() is always inside the polygon; a centroid may not be.
        anchor = polygon.representative_point()
        candidates = pd.DataFrame(
            {
                "station": stations_m["station"],
                "station_inside": stations_m.within(polygon),
                "distance_km": stations_m.distance(anchor) / 1000,
            }
        )
        best = candidates.sort_values(
            ["station_inside", "distance_km"], ascending=[False, True]
        ).iloc[0]
        rows.append(
            {
                "district_id": district_id,
                "district": district,
                "station": best["station"],
                "station_inside": bool(best["station_inside"]),
                "distance_km": round(float(best["distance_km"]), 1),
            }
        )
    return pd.DataFrame(rows)


def district_months(assignment: pd.DataFrame, monthly: pd.DataFrame) -> pd.DataFrame:
    """Give every district its station's monthly series: one row per district per month."""
    table = assignment.merge(monthly, on="station", how="left")
    return table.sort_values(["district_id", "date"], ignore_index=True)
