#!/usr/bin/env bash
set -euo pipefail

docker build -f infras/docker/services/airflow/Dockerfile -t custom-airflow:2.10.3-python3.11 infras/docker/services/airflow
docker build -f infras/docker/services/flink/Dockerfile -t custom-flink:1.20.3 infras/docker/services/flink
docker build -f infras/docker/services/hive/Dockerfile -t custom-hive:4.0.1 infras/docker/services/hive
docker build -f infras/docker/services/postgres/Dockerfile -t custom-postgres:15 infras/docker/services/postgres
docker build -f infras/docker/services/spark/Dockerfile -t custom-spark:3.5.4-java17 infras/docker/services/spark