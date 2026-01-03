#!/bin/bash
set -e

envsubst < /tmp/init-scripts/init.sql.template \
         > /tmp/init-scripts/init.sql

cp /tmp/init-scripts/* /docker-entrypoint-initdb.d/

echo "Initialized SQL script:"
cat /docker-entrypoint-initdb.d/init.sql

exec docker-entrypoint.sh postgres