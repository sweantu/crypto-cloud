from pyspark.errors.exceptions.base import AnalysisException
from pyspark.sql import SparkSession


def get_glue_session(app_name: str, iceberg_lock_table: str) -> SparkSession:
    spark = SparkSession.builder.appName(app_name).config(  # type: ignore
        "spark.sql.session.timeZone", "UTC"
    )
    if iceberg_lock_table:
        spark = (
            spark.config(
                "spark.sql.catalog.glue_catalog",
                "org.apache.iceberg.spark.SparkCatalog",
            )
            .config(
                "spark.sql.catalog.glue_catalog.catalog-impl",
                "org.apache.iceberg.aws.glue.GlueCatalog",
            )
            .config(
                "spark.sql.catalog.glue_catalog.lock.table", f"{iceberg_lock_table}"
            )
        )
    return spark.getOrCreate()


def get_spark_session(app_name: str, iceberg: bool = False) -> SparkSession:
    spark = (
        SparkSession.builder.appName(app_name)  # type: ignore
        # .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        # local mode optimizations to reduce memory consumption
        .config("spark.sql.parquet.enableVectorizedReader", "false")
        .config("spark.sql.columnVector.offheap.enabled", "false")
        .config("spark.memory.offHeap.enabled", "false")
        .config(
            "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
        )
        .config("spark.driver.memory", "2g")
        .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
        .config("spark.sql.codegen.wholeStage", "false")
        # minio specific configs
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config("spark.hadoop.fs.s3a.access.key", "admin")
        .config("spark.hadoop.fs.s3a.secret.key", "admin123")
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
        # .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4")
        .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
    )

    if iceberg:
        spark = (
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
            # .config(
            #     "spark.jars.packages",
            #     ",".join(
            #         [
            #             "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
            #             "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
            #             "org.apache.hadoop:hadoop-aws:3.3.4",
            #         ]
            #     ),
            # )
        )

    return spark.getOrCreate()


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