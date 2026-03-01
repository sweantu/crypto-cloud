from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

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

    aggtrades = GlueJobOperator(
        task_id="aggtrades_glue_job",
        job_name="crypto-cloud-dev-650251698703-aggtrades",
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
        },
        region_name="ap-southeast-1",
        wait_for_completion=True,
        verbose=True,
    )

    end = EmptyOperator(task_id="end")

    (start >> aggtrades >> end)
