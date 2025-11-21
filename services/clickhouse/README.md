```bash
docker exec clickhouse clickhouse-client -u $CLICKHOUSE_USER --password $CLICKHOUSE_PASSWORD --database $CLICKHOUSE_DB --query="SHOW TABLES;"
docker exec -it clickhouse clickhouse-client -u $CLICKHOUSE_USER --password $CLICKHOUSE_PASSWORD --database $CLICKHOUSE_DB
show databases;
show tables in glue_catalog;
select * from glue_catalog.`crypto_cloud_dev_650251698703_serving_db.klines` limit 10;
envsubst < 06_test.sql | docker exec -i clickhouse clickhouse client -n
```
