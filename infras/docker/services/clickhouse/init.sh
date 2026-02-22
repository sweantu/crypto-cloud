#!/usr/bin/env bash
set -euo pipefail

SQL_DIR=./init-scripts

for f in $(ls "$SQL_DIR"/*.sql | sort); do
    echo "Running $f..."

    # Substitute environment variables THEN pipe to clickhouse-client
    envsubst < "$f" \
        | docker exec -i crypto-cloud-clickhouse clickhouse client \
            --user "$CLICKHOUSE_USER" \
            --password "$CLICKHOUSE_PASSWORD" \
            --database "$CLICKHOUSE_DB" \
            -n
done

echo "All SQL scripts executed successfully!"