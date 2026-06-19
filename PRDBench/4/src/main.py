#!/usr/bin/env python3
"""Main entry point for the Satellite Store Business Planning System."""

import sys
from pathlib import Path

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from store_forecasting_tool.cli.menu import run

if __name__ == "__main__":
    run()
