"""The whole pipeline: raw inputs in, two CARTO-ready GeoParquet files out."""

from pathlib import Path

from moldova_drought import config
from moldova_drought.classify import classify_spei
from moldova_drought.districts import assign_stations, district_months, load_districts
from moldova_drought.download import download
from moldova_drought.export import monthly_layer, risk_layer, write_outputs
from moldova_drought.load import load_stations, station_points
from moldova_drought.risk import drought_summary


def run(out_dir: Path = config.PROCESSED_DIR) -> list[Path]:
    """Run every step and return the paths of the files written."""
    download(config.BOUNDARIES_URL, config.BOUNDARIES_GEOJSON, config.BOUNDARIES_SHA256)

    stations = load_stations()
    monthly = stations[["station", "date", "spei_3"]].join(classify_spei(stations["spei_3"]))

    districts = load_districts()
    assignment = assign_stations(districts, station_points(stations))
    table = district_months(assignment, monthly)

    risk = risk_layer(districts, assignment, drought_summary(table))
    return write_outputs(risk, monthly_layer(districts, table), out_dir)
