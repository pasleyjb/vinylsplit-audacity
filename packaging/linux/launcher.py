"""PyInstaller entry point for the VinylSplit Linux bundle."""

from __future__ import annotations

import sys

from vinylsplit.app import main


def run() -> int:
    """Launch VinylSplit and return the process exit code."""
    return main()


if __name__ == "__main__":
    raise SystemExit(run())