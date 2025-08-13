import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict

app = FastAPI()

# Load CSV once API starts up
df = pd.read_csv('Mobile_Food_Facility_Permit.csv')

#Normalize columns that are queried on later ensuring text cols are strings and handle NaNs
for col in ['Applicant', 'Status', 'Address']:
    if col in df.columns:
        df[col] = df[col].fillna('').astype(str)

# Normalize columns that are numeric; coerce invalids to NaN
for col in ['Latitude', 'Longitude']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Pre-filter rows that have valid coordinates
df_with_coordinates = df.dropna(subset=['Latitude', 'Longitude']).copy()
df_with_coordinates = df_with_coordinates[(df_with_coordinates['Latitude'] != 0.0) & (df_with_coordinates['Longitude'] != 0.0)]


@app.get("/search/applicant", response_model=List[Dict])
def search_by_applicant(
    name: str = Query(..., description='Full or partial applicant name'),
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
