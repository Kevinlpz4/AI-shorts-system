"""
Test fixtures for Learning Integration Layer tests.

Provides shared path setup and common utilities.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure src/ is on sys.path for learning.integration imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
