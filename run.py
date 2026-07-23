#!/usr/bin/env python3
"""
AI Shorts System — Runtime launcher.

Usage:
    python run.py list-sources
    python run.py ingest
    python run.py feedback
    python run.py schedule
    python run.py stats
    python run.py cycle
"""
import sys
from pathlib import Path

# Ensure src/ is in the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from runtime.__main__ import main

if __name__ == "__main__":
    main()
