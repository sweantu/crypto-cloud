chmod +x run_clickhouse_init.sh

docker compose exec clickhouse clickhouse-client -u default --password 123456 --database testdb --query="SHOW TABLES;"
