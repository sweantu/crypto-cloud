import logging

from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_prefix = "crypto-cloud-dev-650251698703"
data_lake_bucket_name = "crypto-cloud-dev-650251698703-data-lake-bucket"
data_lake_iceberg_lock_table_name = "crypto_cloud_dev_650251698703_iceberg_lock_table"
data_prefix = project_prefix.replace("-", "_")


spark = (
    SparkSession.builder.appName("Landing Job")  # type: ignore
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.defaultCatalog", "glue_catalog")
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.glue_catalog.catalog-impl",
        "org.apache.iceberg.aws.glue.GlueCatalog",
    )
    .config(
        "spark.sql.catalog.glue_catalog.warehouse",
        f"s3a://{data_lake_bucket_name}/",
    )
    .config(
        "spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO"
    )
    .config(
        "spark.sql.catalog.glue_catalog.lock.table",
        f"{data_lake_iceberg_lock_table_name}",
    )
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
        "org.apache.iceberg:iceberg-aws-bundle:1.6.1,"
        "org.apache.hadoop:hadoop-aws:3.3.4",
    )
    .getOrCreate()
)


test_db = f"{data_prefix}_iceberg_test_db"
spark.sql(f"""
CREATE DATABASE IF NOT EXISTS {test_db}
LOCATION 's3a://{data_lake_bucket_name}/iceberg_test_db/'
""")

spark.sql(f"DROP TABLE IF EXISTS {test_db}.sample_orders")

spark.sql(f"""
CREATE TABLE {test_db}.sample_orders (
    order_id INT,
    product STRING,
    price DOUBLE
) USING iceberg
TBLPROPERTIES ('format-version'='2')
""")

spark.sql(f"""
INSERT INTO {test_db}.sample_orders
VALUES (3, 'BTC', 62500.1), (4, 'ETH', 3100.5)
""")

logger.info("✅ Test Glue job completed successfully")
