```bash
pip install -r requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt"
spark-submit \
    --master "local[*]" \
    --packages org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,org.apache.iceberg:iceberg-aws-bundle:1.7.1 \
    apps/crypto_data/entrypoints/spark_jobs/aggtrades.py \
    --symbol ADAUSDT \
    --landing_date "2025-09-26" \
    --data_lake_bucket $DATA_LAKE_BUCKET \
    --transform_db $TRANSFORM_DB \
    --iceberg_lock_table $ICEBERG_LOCK_TABLE
```
