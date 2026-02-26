docker-network-create:
	docker network create crypto-cloud-network

docker-batch-storage-up:
	docker-compose -p crypto-cloud-batch-storage -f infras/docker/docker-compose.batch-storage.yml up -d --remove-orphans
docker-batch-storage-down:
	docker-compose -p crypto-cloud-batch-storage -f infras/docker/docker-compose.batch-storage.yml down
docker-stream-storage-up:
	docker-compose -p crypto-cloud-stream-storage -f infras/docker/docker-compose.stream-storage.yml up -d --remove-orphans
docker-stream-storage-down:
	docker-compose -p crypto-cloud-stream-storage -f infras/docker/docker-compose.stream-storage.yml down

docker-minio-create-bucket:
	docker exec -i crypto-cloud-minio sh -c '\
		mc alias set local http://localhost:9000 "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" && \
		mc ls local/$(DATA_LAKE_BUCKET) >/dev/null 2>&1 || \
			mc mb local/$(DATA_LAKE_BUCKET) \
	'
docker-clickhouse-client:
	docker exec -it crypto-cloud-clickhouse clickhouse-client -u $$CLICKHOUSE_USER --password $$CLICKHOUSE_PASSWORD --database $$CLICKHOUSE_DB
docker-clickhouse-init:
	bash infras/docker/services/clickhouse/init.sh