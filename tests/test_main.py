import importlib
import sys

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def df_mock():
    # Build a DataFrame that exercises case-insensitive matching and NaN handling
    return pd.DataFrame(
        [
            {
                "Applicant": "Tasty Truck",
                "Status": "APPROVED",
                "Address": "123 SANSOME ST",
                "Latitude": 37.7801,
                "Longitude": -122.401,
            },
            {
                "Applicant": "Another Vendor",
                "Status": "REQUESTED",
                "Address": "500 Market St",
                "Latitude": 0.0,     # invalid coordinates to ensure they are filtered in coord-specific logic
                "Longitude": 0.0,
            },
            {
                "Applicant": "taste of sf",
                "Status": "approved",  # lower-case to test case-insensitive status filter
                "Address": "200 San Bruno Ave",
                "Latitude": 37.765,
                "Longitude": -122.405,
            },
            {
                "Applicant": np.nan,   # NaN text fields should be normalized to empty strings
                "Status": np.nan,
                "Address": np.nan,
                "Latitude": np.nan,
                "Longitude": np.nan,
            },
        ]
    )


@pytest.fixture
def app_module(monkeypatch, df_mock):
    # Patch pandas.read_csv BEFORE importing main to ensure the module’s globals are built from our DataFrame
    monkeypatch.setattr(pd, "read_csv", lambda *_args, **_kwargs: df_mock)

    # Ensure a clean import if something imported main before
    if "main" in sys.modules:
        del sys.modules["main"]
    import main

    main = importlib.reload(sys.modules["main"])
    return main


@pytest.fixture
def client(app_module):
    return TestClient(app_module.app)


def test_search_by_applicant_partial_case_insensitive(client):
    resp = client.get("/search/applicant", params={"name": "tasty"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(row["Applicant"] == "Tasty Truck" for row in data)


def test_search_by_applicant_with_status_filter_case_insensitive(client):
    resp = client.get("/search/applicant", params={"name": "taste", "status": "APPROVED"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["Applicant"] == "taste of sf"


def test_search_by_applicant_not_found_404(client):
    resp = client.get("/search/applicant", params={"name": "nonexistent"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No matching applicant(s) found"


def test_search_by_street_partial_match_case_insensitive(client):
    resp = client.get("/search/street", params={"street": "san"})
    assert resp.status_code == 200
    data = resp.json()
    addresses = {row["Address"] for row in data}
    assert "123 SANSOME ST" in addresses
    assert "200 San Bruno Ave" in addresses


def test_search_by_street_not_found_404(client):
    resp = client.get("/search/street", params={"street": "ZZZ"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No matching addresses found"