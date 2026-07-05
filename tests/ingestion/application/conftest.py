"""
Test fixtures for Ingestion Application Layer tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path for ingestion.application imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
