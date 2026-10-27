"""Fixtures for the plain (non-Django) tests.

These exercise the SQLAlchemy side of the codebase (the cron importer path:
``db.py`` + ``schema/*`` + ``members.py``) against an in-memory SQLite
database.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import db
# Importing the schema modules registers the models on db.Base.
from schema import fee_entry, member, status, transaction  # noqa: F401


@pytest.fixture
def engine():
    return create_engine('sqlite://')


@pytest.fixture
def session(engine):
    db.Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
