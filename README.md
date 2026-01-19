# Crypto Cloud

Crypto Cloud is a data platform for collecting, processing, and serving crypto market data. It supports both batch and streaming workflows, with local Docker stacks for development and Terraform modules for AWS deployment.

## Grafana dashboards

Sample dashboard screenshots:
![Klines dashboard](infras/docker/services/grafana/klines-new-dashboard-2025-12-24-18_01_20.png)

## What this project covers

- Data generation/ingestion (e.g., agg trades producers).
- Stream processing with Flink and batch processing with Spark.
- Data lake storage using S3/MinIO + Iceberg + Hive Metastore.
- Serving layer using ClickHouse.
- Orchestration with Airflow.
- Infrastructure as code via Terraform (VPC, Kinesis, Glue, ECS, Lambda, etc.).

## High-level data flow

1. Producers publish market data into streaming systems.
2. Flink jobs process streams and write to Iceberg tables.
3. Spark/Glue jobs handle batch transformations.
4. ClickHouse serves curated datasets for analytics.

## Repository layout

- `apps/crypto_data`: application code by lifecycle stage (generation, ingestion, transformation, serving, orchestration).
- `apps/shared_lib`: shared Python utilities packaged as a library.
- `infras/docker`: local Docker stacks for storage, batch, and streaming services.
- `infras/terraform`: AWS infrastructure modules and root configs.
- `scripts`: helper scripts (e.g., Docker image builds).
- `build`: build artifacts (e.g., Glue job libraries).

## Local development (Docker)

The docker-compose files expect an external network named `crypto-cloud-network`.

```bash
docker network create crypto-cloud-network
make docker-build
make docker-storage-up
make docker-stream-up
make docker-batch-up
```

Common services:

- Storage: MinIO, Postgres, Hive Metastore, ClickHouse.
- Streaming: Kafka + Kafka UI, Flink JobManager/TaskManager.
- Batch/Orchestration: Spark, Airflow.

To shut stacks down:

```bash
make docker-storage-down
make docker-stream-down
make docker-batch-down
```

## Selected Make targets

- `make tf-init`, `make tf-plan`, `make tf-apply`: manage Terraform in `infras/terraform`.
- `make docker-build`: build custom images for local services.
- `make spark-submit`: run a local Spark job.
- `make invoke-lambda`: invoke a deployed Lambda using `lambda_input.json`.

## Infrastructure (Terraform)

Terraform lives in `infras/terraform` with modules for core AWS services. Typical usage:

```bash
make tf-init
make tf-plan
make tf-apply
```

## Notes

- Update `.env` with credentials and configuration for local stacks.
- App-level entrypoints and examples are under `apps/crypto_data/**/README.md`.
