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

# ── Test database (PostgreSQL) ──
# Setear ANTES de cualquier import para que settings.DATABASE_URL
# lea el valor correcto cuando app.config se importe.
os.environ["DATABASE_URL"] = "postgresql+psycopg2://kevin:1234@localhost:5432/test_system_shorts"

# Load .env for test environment (API keys, etc.)
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
