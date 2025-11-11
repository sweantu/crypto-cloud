#!/usr/bin/env bash
set -e

# Run migrations
airflow db migrate

# Create default admin user if it doesn’t exist
airflow users create \
  --username admin \
  --password admin \
  --firstname Air \
  --lastname Flow \
  --role Admin \
  --email admin@example.com || true

# Start both webserver and scheduler
airflow webserver &
airflow scheduler