from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

# Default DAG args
default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="etl_dag_glue",
    default_args=default_args,
    description="ETL DAG using AWS Glue Job",
    schedule_interval="0 0 * * *",
    start_date=datetime(2025, 9, 27),
    end_date=datetime(2025, 9, 27),
    catchup=True,  # enable backfill
    max_active_runs=1,
    params={
        "symbol": "ADAUSDT",
    },
    tags=["glue", "etl"],
) as dag:
    start = EmptyOperator(task_id="start")

    landing_job = GlueJobOperator(
        task_id="landing_glue_job",
        job_name="crypto-cloud-dev-650251698703-landing-job",
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
            "--project_prefix": "crypto-cloud-dev-650251698703",
            "--data_lake_bucket_name": "crypto-cloud-dev-650251698703-data-lake-bucket",
            "--data_lake_iceberg_lock_table_name": "crypto_cloud_dev_650251698703_iceberg_lock_table",
        },
        region_name="ap-southeast-1",  # change if needed
        aws_conn_id="aws_default",  # connection in Airflow
        wait_for_completion=True,
        verbose=True,
    )

    transform_job = GlueJobOperator(
        task_id="transform_glue_job",
        job_name="crypto-cloud-dev-650251698703-transform-job",
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
            "--project_prefix": "crypto-cloud-dev-650251698703",
            "--data_lake_bucket_name": "crypto-cloud-dev-650251698703-data-lake-bucket",
            "--data_lake_iceberg_lock_table_name": "crypto_cloud_dev_650251698703_iceberg_lock_table",
        },
        region_name="ap-southeast-1",  # change if needed
        aws_conn_id="aws_default",  # connection in Airflow
        wait_for_completion=True,
        verbose=True,
    )

    transform_job_pattern_two = GlueJobOperator(
        task_id="transform_glue_job_pattern_two",
        job_name="crypto-cloud-dev-650251698703-transform-job-pattern-two",
        script_args={
            "--symbol": "{{ params.symbol }}",
            "--landing_date": "{{ ds }}",
            "--project_prefix": "crypto-cloud-dev-650251698703",
            "--data_lake_bucket_name": "crypto-cloud-dev-650251698703-data-lake-bucket",
            "--data_lake_iceberg_lock_table_name": "crypto_cloud_dev_650251698703_iceberg_lock_table",
        },
        region_name="ap-southeast-1",  # change if needed
        aws_conn_id="aws_default",  # connection in Airflow
        wait_for_completion=True,
        verbose=True,
    )

    end = EmptyOperator(task_id="end")

    start >> landing_job >> transform_job >> transform_job_pattern_two >> end
