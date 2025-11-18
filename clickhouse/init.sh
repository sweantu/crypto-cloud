#!/usr/bin/env bash
set -euo pipefail

# Directory containing SQL scripts
SQL_DIR=./init-scripts

# Run each SQL file in order
for f in $(ls "$SQL_DIR"/*.sql | sort); do
    echo "Running $f..."
    docker exec -i clickhouse sh -c "clickhouse-client --user $CLICKHOUSE_USER --password $CLICKHOUSE_PASSWORD --database $CLICKHOUSE_DB" < "$f"
done

echo "All scripts executed!"