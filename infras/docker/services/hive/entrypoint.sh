#!/usr/bin/env bash
set -e

echo "Rendering hive-site.xml from environment variables..."

# Render to temp file (always writable)
envsubst < /opt/hive/conf/hive-site.xml.template \
        > /tmp/hive-site.xml

# Move with correct ownership
install -o 1000 -g 1000 -m 644 /tmp/hive-site.xml \
        /opt/hive/conf/hive-site.xml

echo "Rendered hive-site.xml (sanity check):"
grep -E "ConnectionURL|ConnectionUserName|warehouse.dir" \
     /opt/hive/conf/hive-site.xml || true

# Exec original Hive entrypoint
exec /entrypoint.sh "$@"