"""Tests for download(). No network: urlopen is replaced by a fake for each test."""

import hashlib
import io
from pathlib import Path

import pytest

from moldova_drought.checksums import ChecksumError
from moldova_drought.download import download

CONTENT = b"fake boundary file"
CONTENT_SHA256 = hashlib.sha256(CONTENT).hexdigest()
URL = "https://example.invalid/boundaries.geojson"


def fake_urlopen(url: str, timeout: float) -> io.BytesIO:
    return io.BytesIO(CONTENT)


def failing_urlopen(url: str, timeout: float) -> io.BytesIO:
    raise AssertionError("download() should not touch the network here")


def test_downloads_and_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    dest = tmp_path / "boundaries.geojson"

    download(URL, dest, CONTENT_SHA256)

    assert dest.read_bytes() == CONTENT


def test_skips_download_if_valid_file_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("urllib.request.urlopen", failing_urlopen)
    dest = tmp_path / "boundaries.geojson"
    dest.write_bytes(CONTENT)

    download(URL, dest, CONTENT_SHA256)  # would raise AssertionError if it downloaded

    assert dest.read_bytes() == CONTENT


def test_bad_checksum_raises_and_leaves_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    dest = tmp_path / "boundaries.geojson"

    with pytest.raises(ChecksumError):
        download(URL, dest, "0" * 64)

    assert list(tmp_path.iterdir()) == []
