FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-amazon \
    apache-airflow-providers-apache-spark \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt"

USER root
COPY apps/crypto_data/orchestration/airflow/dags /opt/airflow/dags
COPY apps/shared_lib /opt/airflow/shared_lib
COPY apps/crypto_data/orchestration/airflow/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && chown -R airflow: /opt/airflow/shared_lib /opt/airflow/dags

USER airflow
RUN pip install --no-cache-dir /opt/airflow/shared_lib

CMD ["bash", "-c", "/entrypoint.sh"]