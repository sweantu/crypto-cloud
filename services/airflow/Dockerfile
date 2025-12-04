FROM apache/airflow:2.10.3-python3.11

USER root

RUN apt-get update && apt-get install -y \
    procps \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    boto3 \
    "apache-airflow-providers-amazon" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.11.txt"

USER root

COPY airflow/dags /opt/airflow/dags
COPY services/airflow/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER airflow

CMD ["bash", "-c", "/entrypoint.sh"]