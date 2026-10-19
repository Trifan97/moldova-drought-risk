"""Load the station SPEI table: verify, select columns, build dates, validate."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from moldova_drought import config
from moldova_drought.checksums import verify_sha256

COLUMNS = ["station", "year", "month", "spei_3", "station_lat", "station_lon"]

# SPEI is standardised (mean 0, sd 1): |values| above 5 are fill values or errors, not drought.
SPEI_ABS_MAX = 5.0
# SPEI-3 needs 3 months of data, so each station series starts with 2 missing values.
LEADING_GAP_MONTHS = 2


class DataValidationError(ValueError):
    """The data breaks an assumption the pipeline relies on."""


def read_stations(path: Path, expected_sha256: str) -> pd.DataFrame:
    """Read the station CSV after checking its checksum; keep only the columns we use."""
    verify_sha256(path, expected_sha256)
    df = pd.read_csv(path, usecols=COLUMNS)
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    df = df.drop(columns=["year", "month"])
    return df.sort_values(["station", "date"], ignore_index=True)


def validate_stations(df: pd.DataFrame) -> None:
    """Raise DataValidationError listing every broken assumption, not just the first."""
    problems: list[str] = []

    n_duplicates = df.duplicated(["station", "date"]).sum()
    if n_duplicates:
        problems.append(f"{n_duplicates} duplicate station-month rows")

    # With no duplicates, this row count means every station has every month: no gaps.
    n_months = len(pd.date_range(df["date"].min(), df["date"].max(), freq="MS"))
    expected_rows = df["station"].nunique() * n_months
    if len(df) != expected_rows:
        problems.append(f"expected {expected_rows} rows (stations x months), found {len(df)}")

    n_coords = df.groupby("station")[["station_lat", "station_lon"]].nunique()
    moving = n_coords.index[(n_coords > 1).any(axis=1)].tolist()
    if moving:
        problems.append(f"stations with more than one coordinate pair: {moving}")

    min_lon, min_lat, max_lon, max_lat = config.MOLDOVA_BBOX
    inside = df["station_lon"].between(min_lon, max_lon) & df["station_lat"].between(
        min_lat, max_lat
    )
    outside = sorted(df.loc[~inside, "station"].unique())
    if outside:
        problems.append(f"stations outside Moldova (lat/lon swapped?): {outside}")

    n_implausible = (df["spei_3"].abs() > SPEI_ABS_MAX).sum()
    if n_implausible:
        problems.append(f"{n_implausible} SPEI-3 values beyond +/-{SPEI_ABS_MAX} (fill values?)")

    month_number = df.groupby("station")["date"].rank(method="first")  # 1 = first month
    should_be_missing = month_number <= LEADING_GAP_MONTHS
    n_bad_gaps = (df["spei_3"].isna() != should_be_missing).sum()
    if n_bad_gaps:
        problems.append(
            f"{n_bad_gaps} rows break the rule: SPEI-3 is missing in exactly "
            f"the first {LEADING_GAP_MONTHS} months of each station"
        )

    if problems:
        raise DataValidationError("Station data failed validation:\n- " + "\n- ".join(problems))


def load_stations(
    path: Path = config.STATIONS_CSV, expected_sha256: str = config.STATIONS_CSV_SHA256
) -> pd.DataFrame:
    """Read and validate the station table: one row per station per month."""
    df = read_stations(path, expected_sha256)
    validate_stations(df)
    return df


def station_points(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """One point per station, in longitude/latitude (EPSG:4326)."""
    stations = df.drop_duplicates("station").reset_index(drop=True)
    return gpd.GeoDataFrame(
        stations[["station"]],
        geometry=gpd.points_from_xy(x=stations["station_lon"], y=stations["station_lat"]),
        crs="EPSG:4326",
    )
