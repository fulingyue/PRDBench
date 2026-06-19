"""Root conftest.py — adds src/ to sys.path so internal modules resolve."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
