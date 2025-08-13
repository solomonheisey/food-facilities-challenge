# Mobile Food Facilities API

This project is a FastAPI-based application that provides an API to query mobile food facility permits in San Francisco. It uses the dataset from [San Francisco's Mobile Food Facility Permit](https://data.sfgov.org/Economy-and-Community/Mobile-Food-Facility-Permit/rqzj-sfat/data) to enable searching and filtering of food trucks based on specific criteria.

## Features

The API provides the following endpoints:

1. **Search by Applicant Name**:
   - Endpoint: `GET /search/applicant`
   - Description: Search for food facilities by partial or full applicant name (case-insensitive). Optionally filter by status (e.g., "APPROVED", "REQUESTED").
   - Query Parameters:
     - `name` (required): Full or partial applicant name.
     - `status` (optional): Filter by status (case-insensitive, e.g., "APPROVED").
   - Example: `GET /search/applicant?name=tasty&status=APPROVED`

2. **Search by Street Name**:
   - Endpoint: `GET /search/street`
   - Description: Search for food facilities by partial or full street name in the address field (case-insensitive). For example, searching "SAN" will match "SANSOME ST".
   - Query Parameters:
     - `street` (required): Full or partial street name.
   - Example: `GET /search/street?street=SAN`

3. **Find Nearest Food Trucks**:
   - Endpoint: `GET /search/nearest`
   - Description: Find the 5 nearest food facilities to a given latitude and longitude, using the Haversine formula to calculate great-circle distances in miles. By default, only returns facilities with "APPROVED" status, but can include all statuses if specified. Invalid or zero coordinates are filtered out.
   - Query Parameters:
     - `latitude` (required): Latitude of the reference point.
     - `longitude` (required): Longitude of the reference point.
     - `all_statuses` (optional, default: `false`): If `true`, includes facilities with any status; otherwise, only "APPROVED".
   - Example: `GET /search/nearest?latitude=37.7790&longitude=-122.4010&all_statuses=true`

## Prerequisites

To run this project, you need:

- **Docker**: To build and run the containerized application.
- **Python 3.9+** (if running locally without Docker).
- The `Mobile_Food_Facility_Permit.csv` file, which contains the dataset (included in the repository).

## Setup and Running the Application

### Using Docker

1. **Build the Docker Image**:
   From the folder containing `Dockerfile` and `main.py`, run:
   ```bash
   docker build -t food-facilities-api .
   ```

2. **Run the Container**:
   Run the container and expose port 8000:
   ```bash
   docker run --rm -p 8000:8000 food-facilities-api
   ```

   The API will be available at `http://localhost:8000`.

### Running Locally (Without Docker)

1. **Install Dependencies**:
   Ensure Python 3.9+ is installed, then install the required packages:
   ```bash
   pip install "fastapi[standard]>=0.112" "pandas>=2.2,<3" "numpy>=1.26,<2"
   ```

2. **Run the Application**:
   With `main.py` and `Mobile_Food_Facility_Permit.csv` in the same directory, run:
   ```bash
   fastapi run main.py --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`.

## Testing

The project includes a test suite using `pytest` to verify the functionality of the API. The tests cover:

- Case-insensitive partial matching for applicant and street searches.
- Status filtering for applicant searches.
- 404 error handling for no results.
- Nearest food truck searches, including default APPROVED-only behavior, all-statuses inclusion, and distance ordering.
- Haversine formula correctness (zero distance to self, symmetry, and triangle inequality).

To run the tests locally:

1. Install test dependencies:
   ```bash
   pip install pytest
   ```

2. Run the tests from the project directory:
   ```bash
   pytest
   ```

## Implementation Details

- **Framework**: FastAPI is used for its async support, automatic OpenAPI documentation, and ease of use.
- **Data Processing**: The dataset is loaded into a Pandas DataFrame at startup. Text columns (`Applicant`, `Status`, `Address`) are normalized to strings with NaNs converted to empty strings. Numeric columns (`Latitude`, `Longitude`) are coerced to floats with invalid values set to NaN.
- **Coordinate Filtering**: The `/search/nearest` endpoint uses a pre-filtered DataFrame (`df_with_coordinates`) that excludes rows with missing or zero coordinates to optimize performance.
- **Distance Calculation**: The Haversine formula calculates great-circle distances in miles, ensuring accurate geospatial queries.
- **Error Handling**: The API returns a 404 status code with a descriptive message when no results are found.
- **Docker Configuration**: The Dockerfile uses `python:3.9-slim` for a lightweight image, installs necessary dependencies, and sets up FastAPI to run on port 8000.

## Example API Usage

You can interact with the API using tools like `curl`, Postman, or a web browser. Below are example requests:

1. **Search by Applicant**:
   ```bash
   curl "http://localhost:8000/search/applicant?name=tasty"
   ```

2. **Search by Street**:
   ```bash
   curl "http://localhost:8000/search/street?street=SAN"
   ```

3. **Find Nearest Food Trucks**:
   ```bash
   curl "http://localhost:8000/search/nearest?latitude=37.7790&longitude=-122.4010&all_statuses=true"
   ```

You can also access the interactive API documentation at `http://localhost:8000/docs` when the server is running.

## Notes

- The dataset (`Mobile_Food_Facility_Permit.csv`) must be present in the same directory as `main.py` or included in the Docker image.
- The Haversine formula uses the Earth's radius in miles (3956 miles) to align with common US-based distance measurements.
- The API is designed to handle case-insensitive queries and gracefully manages missing or invalid data in the dataset.