import pytest
from backend.app.main import root, health_check
from backend.app.database.connection import engine

def test_root_endpoint():
    res = root()
    assert res["status"] == "online"
    assert res["app"] == "LeadPilot AI"
    assert res["checkpoint"] == "CP-01"

def test_health_check_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["database"] == f"{engine.dialect.name}_connected"

