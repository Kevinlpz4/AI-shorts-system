#!/usr/bin/env python3
"""
AI Shorts System — Runtime launcher.

Auto-detects the correct Python environment (venv or system).
Usage:
    python run.py list-sources
    python run.py ingest
    python run.py feedback
    python run.py schedule
    python run.py stats
    python run.py cycle
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"
SRC_PATH = str(PROJECT_ROOT / "src")


def ensure_venv():
    """If running outside venv, re-exec with venv Python."""
    try:
        import rich  # noqa: F401
        return  # Already have dependencies
    except ImportError:
        pass

    if VENV_PYTHON.exists():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(PROJECT_ROOT / "run.py")] + sys.argv[1:])
    else:
        print("ERROR: No virtual environment found at .venv/")
        print("Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
        sys.exit(1)


def main():
    sys.path.insert(0, SRC_PATH)
    from runtime.__main__ import main as runtime_main
    runtime_main()


if __name__ == "__main__":
    ensure_venv()
    main()
