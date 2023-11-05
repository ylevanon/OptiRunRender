FROM python:3.8.10

WORKDIR /app

COPY . .

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

ENV GRB_LICENSE_FILE=/app/gurobi.lic

ENV REDIS_URL="redis://redis"