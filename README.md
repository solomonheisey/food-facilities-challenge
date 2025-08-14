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
- The `Mobile_Food_Facility_Permit.csv` file, which contains the dataset (included in the repository or downloadable from the source link above).

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

   The API will be available at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.

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

   The API will be available at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.

## Testing

The project includes a test suite using `pytest` to verify the functionality of the API. The tests cover:

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

## Reasoning Behind Technical/Architectural Decisions

- **Choice of FastAPI**: Selected for its modern asynchronous capabilities, automatic generation of OpenAPI documentation (accessible at `/docs`), and type-safe endpoint definitions. It simplifies development with built-in validation and aligns well with Python's ecosystem for rapid API development.
- **Pandas and NumPy**: Pandas is ideal for handling tabular CSV data, enabling efficient filtering and querying. NumPy supports numerical operations for the Haversine formula. Loading the dataset in-memory at startup avoids repeated file I/O, suitable for the small dataset size (~1-2k rows).
- **Haversine Formula**: Implemented manually to calculate great-circle distances, avoiding external dependencies like Google Maps API, which would introduce latency, costs, and API key management. Haversine is accurate for this use case and uses miles to align with US conventions.
- **No Database**: The dataset is small and static, making an in-memory DataFrame sufficient, lightweight, and fast. A database would add complexity without clear benefits for this scale.
- **Testing with Pytest**: Chosen for its robust features and Python integration. Tests mock the DataFrame to isolate logic, covering edge cases like NaNs, invalid coordinates, and case-insensitive matching.
- **Dockerfile**: Uses `python:3.9-slim` for a minimal image, includes environment variables for Python best practices, and ensures reproducibility across environments.
- **Case-Insensitivity and Partial Matching**: Implemented with string lowercasing and `str.contains` for user-friendly, robust searches that handle real-world input variations.
- **No UI**: Focused on backend requirements, with UI as an optional bonus not implemented due to time constraints.

## Critique Section

### What would you have done differently if you had spent more time on this?
With additional time, I would:
- Develop a React-based frontend UI with Leaflet.js for a map view of food truck locations, enhancing user interaction.
- Implement pagination for endpoints to handle large result sets efficiently.
- Add caching (e.g., Redis) for the `/search/nearest` endpoint to reduce repeated Haversine calculations.
- Integrate a geospatial database like PostgreSQL with PostGIS for faster distance queries.
- Add advanced filters (e.g., by food items or operating hours) for richer querying.
- Include logging (e.g., with Sentry) and monitoring for production reliability.

### What are the trade-offs you might have made?
- **In-Memory Data vs. Database**: In-memory Pandas is fast and simple for small datasets but consumes memory and limits scalability. A database offers persistence and concurrency but adds setup complexity.
- **Haversine vs. External API**: Manual Haversine is lightweight and dependency-free but doesn't account for real-world routing (e.g., roads). Google Maps API could provide driving distances but introduces latency, costs, and external dependency risks.
- **Static CSV vs. Dynamic Fetch**: Loading a static CSV ensures reliability but requires manual updates. Fetching from the SF Gov API at startup ensures fresh data but risks failures if the source is unavailable.
- **No Authentication**: Simplifies the API but leaves it open to abuse; adding JWT or API keys would enhance security at the cost of complexity.

### What are the things you left out?
- Frontend UI (bonus feature).
- Advanced filters (e.g., by food items, operating hours, or permit type).
- Real-time data updates (relies on static CSV, no polling of source API).
- Rate limiting to prevent API abuse.
- Extended error handling for malformed inputs beyond FastAPI's validation.
- Deployment instructions for cloud platforms (e.g., AWS, Heroku).
- Integration tests with the full dataset.

### What are the problems with your implementation and how would you solve them if we had to scale the application to a large number of users?
- **Problems**:
  - **Scalability Limits**: Pandas is single-threaded and memory-intensive; high traffic could cause out-of-memory issues or slow responses for `/search/nearest` due to row-wise Haversine calculations.
  - **Data Freshness**: Static CSV requires manual updates, risking outdated results if the dataset changes frequently.
  - **Performance on Large Datasets**: For datasets growing beyond 10k rows, filtering and sorting could become slow.
  - **Concurrency**: FastAPI is async, but Pandas operations are not parallelized, limiting throughput.
  - **Truncated CSV**: The included `Mobile_Food_Facility_Permit.csv` may be incomplete; users should download the full dataset from the SF Gov source to ensure accuracy.
  - **No Caching**: Repeated nearest queries recompute distances, wasting CPU.
  - **Security**: Limited input sanitization beyond type checking; potential for injection if endpoints are extended.

- **Scaling Solutions**:
  - Migrate to PostgreSQL with PostGIS for geospatial indexing, using `ST_Distance` for efficient nearest-neighbor queries.
  - Implement caching with Redis for frequent queries (e.g., popular lat/long searches).
  - Use Apache Spark for distributed data processing if the dataset grows significantly.
  - Deploy with Kubernetes for horizontal scaling, with load balancers and monitoring via OpenTelemetry.
  - Automate data refreshes by polling the SF Gov API periodically or on startup.
  - Add pagination to all endpoints and optimize DataFrame queries with indexes.
  - Introduce rate limiting (FastAPI middleware) and authentication (JWT) for security.
  - Use a CDN and API gateway for high traffic and global access.

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

Access the interactive API documentation at `http://localhost:8000/docs` when the server is running.

## Notes

- The dataset (`Mobile_Food_Facility_Permit.csv`) must be present in the same directory as `main.py` or included in the Docker image. Ensure you have the full, up-to-date CSV from the SF Gov source (https://data.sfgov.org/Economy-and-Community/Mobile-Food-Facility-Permit/rqzj-sfat/data).
- The Haversine formula uses the Earth's radius in miles (3956 miles) to align with common US-based distance measurements.
- The API is designed to handle case-insensitive queries and gracefully manages missing or invalid data in the dataset.