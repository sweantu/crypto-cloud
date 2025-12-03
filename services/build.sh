#!/usr/bin/env bash
set -euo pipefail

docker build -f spark/Dockerfile -t custom-spark:3.5.4-java17 .

docker build -f hive/Dockerfile -t custom-hive:4.0.1 .