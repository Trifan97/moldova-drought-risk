"""SHA-256 checksums: prove a data file is byte-for-byte the one we expect."""

import hashlib
from pathlib import Path


class ChecksumError(ValueError):
    """A file's SHA-256 does not match the expected value."""


def sha256sum(path: Path) -> str:
    """Return the SHA-256 hex digest of a file (read in chunks, so file size doesn't matter)."""
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verify_sha256(path: Path, expected: str) -> None:
    """Raise ChecksumError if the file's SHA-256 differs from ``expected``."""
    actual = sha256sum(path)
    if actual != expected:
        raise ChecksumError(f"{path.name}: expected SHA-256 {expected}, got {actual}")
