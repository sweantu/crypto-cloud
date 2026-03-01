import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from shared_lib.airflow import require_env
from shared_lib.name import get_glue_job_name

REGION = os.getenv("AWS_REGION", "")

default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="glue",
    default_args=default_args,
    description="ETL DAG using AWS Glue Job",
    schedule_interval=None,
    start_date=datetime(2025, 9, 24),
    catchup=False,
    max_active_runs=1,
    params={
        "symbol": "ADAUSDT",
    },
    tags=["glue", "etl"],
) as dag:
    start = EmptyOperator(task_id="start")

    validate = PythonOperator(
        task_id="validate_env",
        python_callable=lambda: require_env(["PROJECT_PREFIX", "AWS_REGION"]),
    )

    aggtrades = GlueJobOperator(
        task_id="aggtrades_glue_job",
        job_name=get_glue_job_name("aggtrades"),
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name=REGION,
        wait_for_completion=True,
        verbose=True,
    )

    klines = GlueJobOperator(
        task_id="klines_glue_job",
        job_name=get_glue_job_name("klines"),
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name=REGION,
        wait_for_completion=True,
        verbose=True,
    )

    pattern_two = GlueJobOperator(
        task_id="pattern_two_glue_job",
        job_name=get_glue_job_name("pattern_two"),
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name=REGION,
        wait_for_completion=True,
        verbose=True,
    )

    end = EmptyOperator(task_id="end")

    (start >> validate >> aggtrades >> klines >> pattern_two >> end)
