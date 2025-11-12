#!/bin/bash
# run_clickhouse_init.sh

# Set container name (from docker-compose)
CONTAINER_NAME=clickhouse

# ClickHouse credentials
USER=default
PASSWORD=123456
DATABASE=testdb

# Directory containing SQL scripts
SQL_DIR=./init-scripts

# Run each SQL file in order
for f in $(ls "$SQL_DIR"/*.sql | sort); do
    echo "Running $f..."
    docker exec -i $CONTAINER_NAME sh -c "clickhouse-client --user $USER --password $PASSWORD --database $DATABASE" < "$f"
done

echo "All scripts executed!"