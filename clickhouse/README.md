```bash
docker exec clickhouse clickhouse-client -u $CLICKHOUSE_USER --password $CLICKHOUSE_PASSWORD --database $CLICKHOUSE_DB --query="SHOW TABLES;"
```
