"""Raw data is never edited: committed files must match their recorded checksums."""

from moldova_drought import config
from moldova_drought.checksums import sha256sum


def test_stations_csv_is_unchanged() -> None:
    assert sha256sum(config.STATIONS_CSV) == config.STATIONS_CSV_SHA256
