FROM python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY main.py ./
COPY Mobile_Food_Facility_Permit.csv ./

RUN pip install --no-cache-dir \
    "fastapi[standard]>=0.112" \
    "pandas>=2.2,<3" \
    "numpy>=1.26,<2"

EXPOSE 8000

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]