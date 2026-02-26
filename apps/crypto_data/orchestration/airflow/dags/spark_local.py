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
RSI_APP = f"{APP_DIR}/rsi.py"
MACD_APP = f"{APP_DIR}/macd.py"
PATTERN_ONE_APP = f"{APP_DIR}/pattern_one.py"
PATTERN_TWO_APP = f"{APP_DIR}/pattern_two.py"
PATTERN_THREE_APP = f"{APP_DIR}/pattern_three.py"
CONN_ID = "spark_local"
CONFIG = {
    "spark.master": "local[*]",
    "spark.jars.packages": ",".join(
        [
            "org.apache.hadoop:hadoop-aws:3.3.4",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
            "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
        ]
    ),
}

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
        conn_id=CONN_ID,
        application_args=[
            "--symbol",
            "{{ params.symbol }}",
            "--landing_date",
            "{{ ds }}",
            "--data_lake_bucket",
            DATA_LAKE_BUCKET,
        ],
        conf=CONFIG,
        verbose=True,
    )

    klines = SparkSubmitOperator(
        task_id="klines_spark_local",
        application=KLINES_APP,
        name="klines",
        conn_id=CONN_ID,
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
        conf=CONFIG,
        verbose=True,
    )

    rsi = SparkSubmitOperator(
        task_id="rsi_spark_local",
        application=RSI_APP,
        name="rsi",
        conn_id=CONN_ID,
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
        conf=CONFIG,
        verbose=True,
    )

    macd = SparkSubmitOperator(
        task_id="macd_spark_local",
        application=MACD_APP,
        name="macd",
        conn_id=CONN_ID,
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
        conf=CONFIG,
        verbose=True,
    )

    indicators_done = EmptyOperator(task_id="indicators_done")

    pattern_one = SparkSubmitOperator(
        task_id="pattern_one_spark_local",
        application=PATTERN_ONE_APP,
        name="pattern_one",
        conn_id=CONN_ID,
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
        conf=CONFIG,
        verbose=True,
    )

    pattern_two = SparkSubmitOperator(
        task_id="pattern_two_spark_local",
        application=PATTERN_TWO_APP,
        name="pattern_two",
        conn_id=CONN_ID,
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
        conf=CONFIG,
        verbose=True,
    )

    pattern_three = SparkSubmitOperator(
        task_id="pattern_three_spark_local",
        application=PATTERN_THREE_APP,
        name="pattern_three",
        conn_id=CONN_ID,
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
        conf=CONFIG,
        verbose=True,
    )

    end = EmptyOperator(task_id="end")

    start >> aggtrades >> klines

    klines >> [rsi, macd] >> indicators_done

    indicators_done >> [pattern_one, pattern_two, pattern_three]

    [pattern_one, pattern_two, pattern_three] >> end
