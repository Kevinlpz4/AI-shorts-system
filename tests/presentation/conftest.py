"""
Presentation Test Fixtures
==========================
Configura test_system_shorts con schema actualizado, limpia tablas antes de cada test.
El env var DATABASE_URL se setea en tests/conftest.py (raíz).
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from infrastructure.persistence.models import Base


TEST_DATABASE_URL = "postgresql+psycopg2://kevin:1234@localhost:5432/test_system_shorts"


@pytest.fixture(scope="module", autouse=True)
def ensure_schema():
    """
    Module-scoped: dropea y recrea tablas UNA VEZ por módulo de tests.
    Así refleja siempre el schema actual de models.py.
    """
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_test_db():
    """
    Function-scoped: trunca todas las tablas antes de CADA test.
    """
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        session.execute(text("TRUNCATE TABLE scheduler_config, research_topics, scripts RESTART IDENTITY CASCADE"))
        session.commit()
    engine.dispose()
