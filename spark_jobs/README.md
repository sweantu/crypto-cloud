```bash
spark-submit \
	--master "local[*]" \
    --packages org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,org.apache.iceberg:iceberg-aws-bundle:1.7.1 \
    --py-files ../build/glue_job_libs/extra.zip \
    jobs/landing/aggtrades.py \
    --symbol "ADAUSDT" \
    --landing_date "2025-10-02" \
    --project_prefix_underscore $PROJECT_PREFIX_UNDERSCORE \
    --data_lake_bucket $DATA_LAKE_BUCKET \
    --iceberg_lock_table $ICEBERG_LOCK_TABLE
```
