"""Smoke test: the package is installed and importable."""

import moldova_drought


def test_package_imports() -> None:
    assert moldova_drought.__name__ == "moldova_drought"
