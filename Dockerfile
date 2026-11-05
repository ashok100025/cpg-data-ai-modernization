# Containerised run path: only Docker is needed on the reviewer's machine.
#   docker build -t cpg-data-ai-poc .   &&   docker run --rm cpg-data-ai-poc
FROM python:3.11.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Makefile uses the system interpreter inside the image instead of a virtualenv
ENV PY=python DBT=dbt CPG_PLANNER=rules

# Full run: data -> bronze/silver/gold/marts -> forecast -> all tests -> AI demo -> summary
CMD ["sh", "-c", "make all && make demo-incremental && make ai-demo && make inspect"]
