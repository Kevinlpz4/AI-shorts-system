"""
Runtime persistence package — SQLAlchemy models and engine factory.

Usage::

    from runtime.persistence.engine import RuntimeEngine

    engine = RuntimeEngine("sqlite:///:memory:")
    engine.create_tables()
    session = engine.get_session()
"""
from __future__ import annotations
