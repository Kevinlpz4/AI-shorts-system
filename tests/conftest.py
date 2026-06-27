"""
Pytest configuration for AI Shorts System.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env for test environment (API keys, etc.)
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
