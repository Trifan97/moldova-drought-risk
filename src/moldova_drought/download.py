"""Download external inputs into data/external/, verified by checksum.

Run with: python -m moldova_drought.download
"""

import shutil
import urllib.request
from pathlib import Path

from moldova_drought import config
from moldova_drought.checksums import ChecksumError, sha256sum, verify_sha256


def download(url: str, dest: Path, expected_sha256: str) -> Path:
    """Download ``url`` to ``dest``, unless a copy with the expected checksum is already there.

    The file is first written to ``<dest>.part`` and only renamed to ``dest`` once its
    checksum matches, so ``dest`` is never a half-downloaded or wrong file.
    """
    if dest.exists() and sha256sum(dest) == expected_sha256:
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(url, timeout=60) as response, part.open("wb") as out:
        shutil.copyfileobj(response, out)

    try:
        verify_sha256(part, expected_sha256)
    except ChecksumError:
        part.unlink()
        raise
    part.replace(dest)
    return dest


def main() -> None:
    path = download(config.BOUNDARIES_URL, config.BOUNDARIES_GEOJSON, config.BOUNDARIES_SHA256)
    print(f"Boundaries ready: {path}")


if __name__ == "__main__":
    main()
