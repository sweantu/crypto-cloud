import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

ROOT_DIR = os.getenv("ROOT_DIR", "/opt/airflow")
DATA_LAKE_BUCKET = os.getenv("DATA_LAKE_BUCKET", "crypto-data-lake")
TRANSFORM_DB = os.getenv("TRANSFORM_DB", "crypto_transform_db")
ICEBERG_LOCK_TABLE = os.getenv("ICEBERG_LOCK_TABLE", "iceberg_lock_table")

APP_DIR = f"{ROOT_DIR}/apps/crypto_data/entrypoints/spark_jobs"
AGGTRADES_APP = f"{APP_DIR}/aggtrades.py"
KLINES_APP = f"{APP_DIR}/klines.py"
PATTERN_TWO_APP = f"{APP_DIR}/pattern_two.py"

default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="spark_local",
    default_args=default_args,
    description="ETL DAG using Spark on localhost",
    schedule_interval="0 0 * * *",
    start_date=datetime(2025, 9, 24),
    catchup=False,
    max_active_runs=1,
    params={
        "symbol": "ADAUSDT",
    },
    tags=["spark", "etl", "local"],
) as dag:
    start = EmptyOperator(task_id="start")

    aggtrades = SparkSubmitOperator(
        task_id="aggtrades_spark_local",
        application=AGGTRADES_APP,
        name="aggtrades",
        conn_id="spark_local",
        application_args=[
            "--symbol",
            "{{ params.symbol }}",
            "--landing_date",
            "{{ ds }}",
            "--data_lake_bucket",
            DATA_LAKE_BUCKET,
        ],
        conf={
            "spark.master": "local[*]",
            "spark.jars.packages": "org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,org.apache.iceberg:iceberg-aws-bundle:1.7.1",
        },
        verbose=True,
    )

    klines = SparkSubmitOperator(
        task_id="klines_spark_local",
        application=KLINES_APP,
        name="klines",
        conn_id="spark_local",
        application_args=[
            "--symbol",
            "{{ params.symbol }}",
            "--landing_date",
            "{{ ds }}",
            "--data_lake_bucket",
            DATA_LAKE_BUCKET,
            "--transform_db",
            TRANSFORM_DB,
            "--iceberg_lock_table",
            ICEBERG_LOCK_TABLE,
        ],
        conf={
            "spark.master": "local[*]",
            "spark.jars.packages": "org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,org.apache.iceberg:iceberg-aws-bundle:1.7.1",
        },
        verbose=True,
    )

    pattern_two = SparkSubmitOperator(
        task_id="pattern_two_spark_local",
        application=PATTERN_TWO_APP,
        name="pattern_two",
        conn_id="spark_local",
        application_args=[
            "--symbol",
            "{{ params.symbol }}",
            "--landing_date",
            "{{ ds }}",
            "--data_lake_bucket",
            DATA_LAKE_BUCKET,
            "--transform_db",
            TRANSFORM_DB,
            "--iceberg_lock_table",
            ICEBERG_LOCK_TABLE,
        ],
        conf={
            "spark.master": "local[*]",
            "spark.jars.packages": "org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,org.apache.iceberg:iceberg-aws-bundle:1.7.1",
        },
        verbose=True,
    )

    end = EmptyOperator(task_id="end")

    start >> aggtrades >> klines >> pattern_two >> end
