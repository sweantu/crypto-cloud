import os

from pyspark.errors.exceptions.base import AnalysisException
from pyspark.sql import SparkSession


def get_spark_session(
    app_name: str,
    master: bool = False,
    local: bool = False,
    minio: bool = False,
    hive: bool = False,
    jars: bool = False,
    glue: bool = False,
    iceberg_lock_table: str | None = None,
) -> SparkSession:

    spark = SparkSession.builder.appName(app_name).config(  # type: ignore
        "spark.sql.session.timeZone", "UTC"
    )

    if master:
        spark = add_master_config(spark)
    if local:
        spark = add_local_config(spark)
    if minio:
        spark = add_minio_config(spark)
    if hive:
        spark = add_hive_catalog_config(spark)

    if jars:
        spark = add_jars_config(spark)

    if glue:
        if not iceberg_lock_table:
            raise ValueError("iceberg_lock_table must be provided when glue is True")
        spark = add_glue_catalog_config(spark, iceberg_lock_table)

    return spark.getOrCreate()

def add_master_config(
    spark: SparkSession.Builder, config: str = "local[*]"
) -> SparkSession.Builder:
    return spark.master(config)


def add_local_config(spark: SparkSession.Builder) -> SparkSession.Builder:
    # local mode optimizations to reduce memory consumption
    return (
        spark.config("spark.sql.parquet.enableVectorizedReader", "false")
        .config("spark.sql.columnVector.offheap.enabled", "false")
        .config("spark.memory.offHeap.enabled", "false")
        .config(
            "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
        )
        .config("spark.driver.memory", "2g")
        .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
        .config("spark.sql.codegen.wholeStage", "false")
    )


def add_minio_config(spark: SparkSession.Builder) -> SparkSession.Builder:
    # minio specific configs
    return (
        spark.config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            f"{os.getenv('MINIO_USER', 'admin')}",
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            f"{os.getenv('MINIO_PASSWORD', 'admin123')}",
        )
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
        .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
    )


def add_hive_catalog_config(spark: SparkSession.Builder) -> SparkSession.Builder:
    return (
        spark.config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(
            "spark.sql.catalog.hive_catalog",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        .config(
            "spark.sql.catalog.hive_catalog.catalog-impl",
            "org.apache.iceberg.hive.HiveCatalog",
        )
        .config(
            "spark.sql.catalog.hive_catalog.uri",
            "thrift://localhost:9083",
        )
    )


def add_glue_catalog_config(
    spark: SparkSession.Builder, iceberg_lock_table: str
) -> SparkSession.Builder:
    return (
        spark.config(
            "spark.sql.catalog.glue_catalog",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        .config(
            "spark.sql.catalog.glue_catalog.catalog-impl",
            "org.apache.iceberg.aws.glue.GlueCatalog",
        )
        .config("spark.sql.catalog.glue_catalog.lock.table", f"{iceberg_lock_table}")
    )

def add_jars_config(spark: SparkSession.Builder) -> SparkSession.Builder:
    return spark.config(
        "spark.jars.packages",
        ",".join(
            [
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
                "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
                "org.apache.hadoop:hadoop-aws:3.3.4",
            ]
        ),
    )


def table_exists(spark: SparkSession, database: str, table: str) -> bool:
    try:
        spark.catalog.getTable(f"{database}.{table}")
        return True
    except AnalysisException:
        return False


def database_exists(spark: SparkSession, database: str) -> bool:
    try:
        spark.catalog.getDatabase(database)
        return True
    except AnalysisException:
        return False


def create_database(spark: SparkSession, database: str, location: str) -> None:
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {database} LOCATION '{location}'")