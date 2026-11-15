import pytest
from sqlalchemy import create_engine
from backend.app.database.connection import _normalize_database_url


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        ("postgres://user:pass@db.example.test/app", "postgresql+psycopg://user:pass@db.example.test/app"),
        ("postgresql://user:pass@db.example.test/app?sslmode=require", "postgresql+psycopg://user:pass@db.example.test/app?sslmode=require"),
        ("sqlite:///./leadpilot.db", "sqlite:///./leadpilot.db"),
    ],
)
def test_normalize_database_url(database_url, expected):
    assert _normalize_database_url(database_url) == expected


def test_normalized_supabase_url_uses_postgresql_dialect():
    database_engine = create_engine(
        _normalize_database_url("postgresql://user:pass@db.example.test/app")
    )
    try:
        assert database_engine.dialect.name == "postgresql"
    finally:
        database_engine.dispose()
