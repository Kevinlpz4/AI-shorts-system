"""
Pytest configuration for foundation tests.

Adds src/ to sys.path so that `from foundation import ...` works
without requiring an editable install.
"""
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
