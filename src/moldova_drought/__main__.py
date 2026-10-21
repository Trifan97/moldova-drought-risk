"""Entry point, so the pipeline runs with: python -m moldova_drought"""

from moldova_drought.pipeline import run


def main() -> None:
    for path in run():
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
