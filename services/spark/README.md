spark.sql.catalog.iceberg = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.iceberg.type = hive
spark.sql.catalog.iceberg.uri = thrift://hive-metastore:9083
spark.sql.catalog.iceberg.warehouse = s3a://iceberg/warehouse

spark.hadoop.fs.s3a.endpoint = http://minio:9000
spark.hadoop.fs.s3a.access.key = minio
spark.hadoop.fs.s3a.secret.key = minio123
spark.hadoop.fs.s3a.path.style.access = true
spark.hadoop.fs.s3a.connection.ssl.enabled = false