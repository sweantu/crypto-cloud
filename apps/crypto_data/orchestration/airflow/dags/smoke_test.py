from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def hello_airflow():
    print("✅ Airflow is working correctly!")
    return "success"


with DAG(
    dag_id="smoke_test",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # manual trigger only
    catchup=False,
    tags=["smoke-test", "local"],
) as dag:
    hello = PythonOperator(
        task_id="hello_airflow",
        python_callable=hello_airflow,
    )

    hello
