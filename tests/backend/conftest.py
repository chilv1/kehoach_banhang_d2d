"""Shared pytest fixtures.

Each test gets a fresh SQLite-in-memory database with both the MS-Project
models and the sales-planner models registered, so service-layer code can be
exercised without spinning up Postgres.
"""
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def db():
    from app.db.session import Base
    from app import models as _ms_models                 # noqa: F401
    from app.sales_planner import models as _sales_models  # noqa: F401

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def excel_bytes() -> bytes:
    path = BACKEND_ROOT.parent / "Campana Plan.xlsx"
    return path.read_bytes()
