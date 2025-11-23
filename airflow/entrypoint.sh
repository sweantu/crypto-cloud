#!/usr/bin/env bash
set -euo pipefail

# Run migrations
airflow db migrate

# Create default admin user if it doesn’t exist
airflow users create \
  --username "${AIRFLOW_ADMIN_USERNAME}" \
  --password "${AIRFLOW_ADMIN_PASSWORD}" \
  --firstname Air \
  --lastname Flow \
  --role Admin \
  --email "${AIRFLOW_ADMIN_EMAIL}" || true

# Start both webserver and scheduler
airflow webserver &
airflow scheduler