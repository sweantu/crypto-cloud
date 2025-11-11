# --- Base image: Airflow 2.9.3 (Python 3.11) ---
FROM apache/airflow:2.9.3-python3.11

USER root

RUN apt-get update && apt-get install -y \
    procps \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

# --- Install Python libraries ---
RUN pip install --no-cache-dir \
    boto3 \
    "apache-airflow-providers-amazon" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"

USER root

COPY dags /opt/airflow/dags
# --- Copy entrypoint ---
COPY docker/airflow.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER airflow

CMD ["bash", "-c", "/entrypoint.sh"]