import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict
from math import radians, cos, sin, asin, sqrt

app = FastAPI()

# Load CSV once API starts up
df = pd.read_csv("Mobile_Food_Facility_Permit.csv")

#Normalize columns that are queried on later ensuring text cols are strings and handle NaNs
for col in ["Applicant", "Status", "Address"]:
    if col in df.columns:
        df[col] = df[col].fillna("").astype(str)

# Normalize columns that are numeric; coerce invalids to NaN
for col in ["Latitude", "Longitude"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Pre-filter rows that have valid coordinates
df_with_coordinates = df.dropna(subset=["Latitude", "Longitude"]).copy()
df_with_coordinates = df_with_coordinates[(df_with_coordinates["Latitude"] != 0.0) & (df_with_coordinates["Longitude"] != 0.0)]

def haversine(lat1: float, lon1: float, lat2: float, lon2: float):
    """
    Calculate the great-circle distance in miles between two points on the Earth using the Haversine formula. Distance is calculated in miles.
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Earth radius in miles
    R = 3956

    # Haversine formula
    long_dist = lon2 - lon1
    lat_dist = lat2 - lat1
    a = sin(lat_dist/2)**2 + cos(lat1) * cos(lat2) * sin(long_dist/2)**2
    c = 2 * asin(sqrt(a))

    return c * R

@app.get("/search/applicant", response_model=List[Dict])
def search_by_applicant(
    name: str = Query(..., description="Full or partial applicant name"),
    status: Optional[str] = Query(
        None,
        description='Optional status filter (e.g., "APPROVED", "REQUESTED"). Case-insensitive.',
    ),
):
    """
        Search by name of applicant (case-insensitive, partial match).
        Optional "status" filter (case-insensitive).
    """
    name_lowercase = name.lower()
    results = df[df["Applicant"].str.lower().str.contains(name_lowercase, na=False)]

    if status:
        status_lower = status.lower()
        results = results[results['Status'].str.lower() == status_lower]

    records = results.to_dict('records')
    if not records:
        raise HTTPException(status_code=404, detail="No matching applicant(s) found")
    return records

@app.get("/search/street", response_model=List[Dict])
def search_by_street(
    street: str = Query(..., description="Full or partial street text (e.g., 'SAN')")
):
    """
        Search by street; matches any part of the Address field (case-insensitive).
        Example: 'SAN' should match 'SANSOME ST'.
    """
    street_lowercase = street.lower()
    results = df[df["Address"].str.lower().str.contains(street_lowercase, na=False)]

    records = results.to_dict('records')

    if not records:
        raise HTTPException(status_code=404, detail="No matching addresses found")
    return records

@app.get("/search/nearest", response_model=List[Dict])
def get_nearest_food_trucks(
    latitude: float = Query(..., description="Latitude of the reference point"),
    longitude: float = Query(..., description="Longitude of the reference point"),
    all_statuses: bool = Query(
        False,
        description="If true, include all statuses; otherwise, only APPROVED"
    )
):
    """
    Return the 5 nearest food facilities given a latitude and longitude.
    By default, only returns facilities with status APPROVED.
    If all_statuses are True, includes all statuses.
    Filters out entries with invalid (0) or missing coordinates.
    """
    # Filter based on status
    results = df_with_coordinates.copy()
    if not all_statuses:
        results = results[results["Status"].str.lower() == "approved"]

    # Calculate distances using Haversine formula
    results["distance"] = results.apply(
        lambda row: haversine(latitude, longitude, row["Latitude"], row["Longitude"]),
        axis=1
    )

    # Sort by distance and take the top 5
    results = results.sort_values(by="distance").head(5)

    # Remove the temporary distance column
    results = results.drop(columns=["distance"])

    records = results.to_dict("records")
    if not records:
        raise HTTPException(status_code=404, detail="No food trucks found with valid coordinates")
    return records
