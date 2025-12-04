#!/usr/bin/env bash
set -euo pipefail

docker build -f services/spark/Dockerfile -t custom-spark:3.5.4-java17 .
    
docker build -f services/hive/Dockerfile -t custom-hive:4.0.1 .

docker build -f services/airflow/Dockerfile -t custom-airflow:2.10.3-python3.11 .

docker build -f services/flink/Dockerfile -t custom-flink:1.20.3-java11 .