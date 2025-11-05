#### run job

```bash
jupyter nbconvert --to script end_landing_job.ipynb

spark-submit \
  --master "local[*]" \
  --driver-memory 2g \
  --conf spark.sql.session.timeZone=UTC \
  --conf spark.sql.sources.partitionOverwriteMode=dynamic \
  --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
  --conf spark.sql.defaultCatalog=glue_catalog \
  --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog \
  --conf spark.sql.catalog.glue_catalog.warehouse=s3a://crypto-cloud-dev-583323753643-data-lake-bucket/ \
  --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.glue_catalog.lock.table=crypto_cloud_dev_583323753643_iceberg_lock_table \
  --conf spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled=false \
  --conf spark.sql.parquet.enableVectorizedReader=false \
  --conf spark.sql.columnVector.offheap.enabled=false \
  --conf spark.memory.offHeap.enabled=false \
  --conf spark.sql.codegen.wholeStage=false \
  --conf spark.driver.extraJavaOptions="-XX:MaxDirectMemorySize=1g" \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,\
org.apache.iceberg:iceberg-aws-bundle:1.6.1,\
org.apache.hadoop:hadoop-aws:3.3.4 \
  landing_job.py
```
