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
                "Applicant": "Pending Cart",
                "Status": "REQUESTED",
                "Address": "1 Dr Carlton B Goodlett Pl",
                "Latitude": 37.7810,
                "Longitude": -122.3990,
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
    import main # noqa: F401

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

def test_nearest_defaults_to_approved_only_and_orders_by_distance(client):
    # Reference point near "Tasty Truck" should list it first when filtering to approve
    resp = client.get("/search/nearest", params={"latitude": 37.7790, "longitude": -122.4010})
    assert resp.status_code == 200
    data = resp.json()
    # Only approved entries should be present by default
    statuses = {row["Status"].lower() for row in data}
    assert statuses <= {"approved"}
    # Nearest should be Tasty Truck for this reference point
    assert data[0]["Applicant"] == "Tasty Truck"
    # Limit to at most 5 entries
    assert len(data) <= 5


def test_nearest_with_all_statuses_includes_non_approved(client):
    # With all_statuses=True, entries like "Pending Cart" (REQUESTED) with valid coords should be included
    resp = client.get(
        "/search/nearest",
        params={"latitude": 37.7790, "longitude": -122.4010, "all_statuses": "true"},
    )
    assert resp.status_code == 200
    data = resp.json()
    applicants = {row["Applicant"] for row in data}
    assert "Pending Cart" in applicants
    assert "Tasty Truck" in applicants


def test_nearest_returns_404_when_no_approved_with_valid_coords(monkeypatch):
    # Build a dataset with valid coords but no APPROVED rows to trigger 404 in default mode
    df_no_approved = pd.DataFrame(
        [
            {"Applicant": "Only Pending", "Status": "REQUESTED", "Address": "A", "Latitude": 37.78, "Longitude": -122.40},
            {"Applicant": "Only Denied", "Status": "DENIED", "Address": "B", "Latitude": 37.77, "Longitude": -122.41},
        ]
    )

    # Build a fresh client with this dataset
    monkeypatch.setattr(pd, "read_csv", lambda *_a, **_k: df_no_approved)
    if "main" in sys.modules:
        del sys.modules["main"]
    import main as _main  # noqa: F401
    _main = importlib.reload(sys.modules["main"])
    client = TestClient(_main.app)

    # Default (approved-only) should yield 404
    resp = client.get("/search/nearest", params={"latitude": 37.779, "longitude": -122.401})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No food trucks found with valid coordinates"

    # But if all_statuses=True, it should return the nearest non-approved entries
    resp2 = client.get(
        "/search/nearest",
        params={"latitude": 37.779, "longitude": -122.401, "all_statuses": "true"},
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) > 0


def test_haversine_zero_and_symmetry(app_module):
    # Distance to self is zero
    d0 = app_module.haversine(37.78, -122.40, 37.78, -122.40)
    assert d0 == 0

    # Symmetry: d(A,B) == d(B,A)
    a = (37.7801, -122.401)
    b = (37.7650, -122.405)
    d_ab = app_module.haversine(a[0], a[1], b[0], b[1])
    d_ba = app_module.haversine(b[0], b[1], a[0], a[1])
    assert pytest.approx(d_ab, rel=1e-9) == d_ba

    # Triangle inequality (weak check): distance to a farther point should be larger
    c = (37.7000, -122.5100)  # farther away
    d_ac = app_module.haversine(a[0], a[1], c[0], c[1])
    assert d_ac > d_ab