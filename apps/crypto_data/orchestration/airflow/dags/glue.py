import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowFailException
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

LANDING_JOB = os.getenv("GLUE_LANDING_JOB", "crypto_landing_job")
TRANSFORM_JOB = os.getenv("GLUE_TRANSFORM_JOB", "crypto_transform_job")
TRANSFORM_JOB_PATTERN_TWO = os.getenv(
    "GLUE_TRANSFORM_JOB_PATTERN_TWO", "crypto_transform_job_pattern_two"
)


def validate_env():
    required = [
        "GLUE_LANDING_JOB",
        "GLUE_TRANSFORM_JOB",
        "GLUE_TRANSFORM_JOB_PATTERN_TWO",
    ]
    for key in required:
        if not os.getenv(key):
            raise AirflowFailException(f"Missing env var: {key}")


# Default DAG args
default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="glue",
    default_args=default_args,
    description="ETL DAG using AWS Glue Job",
    schedule_interval="0 0 * * *",
    start_date=datetime(2025, 9, 24),
    catchup=False,  # enable backfill
    max_active_runs=1,
    params={
        "symbol": "ADAUSDT",
    },
    tags=["glue", "etl"],
) as dag:
    start = EmptyOperator(task_id="start")

    validate = PythonOperator(
        task_id="validate_env",
        python_callable=validate_env,
    )

    landing_job = GlueJobOperator(
        task_id="landing_glue_job",
        job_name=LANDING_JOB,
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name="ap-southeast-1",  # change if needed
        aws_conn_id="aws_default",  # connection in Airflow
        wait_for_completion=True,
        verbose=True,
    )

    transform_job = GlueJobOperator(
        task_id="transform_glue_job",
        job_name=TRANSFORM_JOB,
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name="ap-southeast-1",  # change if needed
        aws_conn_id="aws_default",  # connection in Airflow
        wait_for_completion=True,
        verbose=True,
    )

    transform_job_pattern_two = GlueJobOperator(
        task_id="transform_glue_job_pattern_two",
        job_name=TRANSFORM_JOB_PATTERN_TWO,
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name="ap-southeast-1",  # change if needed
        aws_conn_id="aws_default",  # connection in Airflow
        wait_for_completion=True,
        verbose=True,
    )

    end = EmptyOperator(task_id="end")

    (
        start
        >> validate
        >> landing_job
        >> transform_job
        >> transform_job_pattern_two
        >> end
    )
