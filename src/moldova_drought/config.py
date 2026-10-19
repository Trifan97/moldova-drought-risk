"""Project paths, data sources and their expected checksums: one source of truth."""

from pathlib import Path

# This file is src/moldova_drought/config.py, so parents[2] is the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"

# Synthetic station data, committed to the repo (see README > Data).
STATIONS_CSV = RAW_DIR / "synthetic_station_spei.csv"
STATIONS_CSV_SHA256 = "42441da3ecf2c77c780d775bee9fe5c04cf320ac72043d95b41ccaee86f631d9"

# geoBoundaries gbOpen ADM1 for Moldova (source: UNHCR, OCHA FISS; licence: CC BY 3.0 IGO).
# The URL pins geoBoundaries commit 9469f09; the checksum proves we got exactly that file.
BOUNDARIES_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/MDA/ADM1/geoBoundaries-MDA-ADM1.geojson"
)
BOUNDARIES_GEOJSON = EXTERNAL_DIR / "geoBoundaries-MDA-ADM1.geojson"
BOUNDARIES_SHA256 = "2358d3f23e7199eb8296d8859c09640c4db9f0a9cef31a429708015ee0aea9b6"
