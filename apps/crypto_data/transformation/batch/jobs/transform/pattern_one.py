# import argparse
import logging
import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession, types
from spark_jobs.common.ema import make_ema_in_chunks
from spark_jobs.common.table import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

args = getResolvedOptions(
    sys.argv,
    [
        "symbol",
        "landing_date",
        "transform_db",
        "data_lake_bucket",
        "iceberg_lock_table",
    ],
)

# parser = argparse.ArgumentParser()
# parser.add_argument("--symbol", required=True)
# parser.add_argument("--landing_date", required=True)
# parser.add_argument("--transform_db", required=True)
# parser.add_argument("--data_lake_bucket", required=True)
# parser.add_argument("--iceberg_lock_table", required=True)
# args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]
logger.info(f"Transforming symbol={symbol} for date={landing_date}")

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
TRANSFORM_DB = args["transform_db"]


spark = (
    SparkSession.builder.appName("TransformZone Pattern One")  # type: ignore
    .config("spark.sql.session.timeZone", "UTC")
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.glue_catalog.catalog-impl",
        "org.apache.iceberg.aws.glue.GlueCatalog",
    )
    .config("spark.sql.catalog.glue_catalog.lock.table", f"{ICEBERG_LOCK_TABLE}")
    # Disable vectorized reader
    # .config("spark.sql.parquet.enableVectorizedReader", "false")
    # .config("spark.sql.columnVector.offheap.enabled", "false")
    # .config("spark.memory.offHeap.enabled", "false")
    # .config(
    #     "spark.sql.catalog.glue_catalog.read.parquet.vectorization.enabled", "false"
    # )
    # .config("spark.driver.memory", "2g")
    # .config("spark.driver.extraJavaOptions", "-XX:MaxDirectMemorySize=1g")
    # .config("spark.sql.codegen.wholeStage", "false")
    # .config(
    #     "spark.jars.packages",
    #     ",".join(
    #         [
    #             "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1",
    #             "org.apache.iceberg:iceberg-aws-bundle:1.7.1",
    #         ]
    #     ),
    # )
    .getOrCreate()
)


transform_db = f"glue_catalog.{TRANSFORM_DB}"
klines_table = "klines"
sql_stmt = f"""
select * from {transform_db}.{klines_table}
where landing_date = DATE('{landing_date}') AND symbol = '{symbol}'
"""
df_sorted = (
    spark.sql(sql_stmt)
    .coalesce(1)  # one partition, not shuffle
    .sortWithinPartitions("group_id")
)
logger.info(f"Input rows: {df_sorted.count()}")

schema = types.StructType(
    [
        *df_sorted.schema.fields,  # keep all original fields
        types.StructField("ema7", types.DoubleType(), True),
        types.StructField("ema20", types.DoubleType(), True),
    ]
)

pattern_one_table = "pattern_one"
if table_exists(spark, transform_db, pattern_one_table):
    sql_stmt = f"""
    select ema7, ema20 from {transform_db}.{pattern_one_table}
    where landing_date = date_sub(DATE('{landing_date}'), 1) AND symbol = '{symbol}'
    order by group_id desc
    limit 1
    """
    row = spark.sql(sql_stmt).first()
    prev_ema7, prev_ema20 = (row["ema7"], row["ema20"]) if row else (None, None)
else:
    prev_ema7, prev_ema20 = None, None

ema_in_chunks_with_state = make_ema_in_chunks(prev_ema7, prev_ema20)

df = df_sorted.mapInPandas(ema_in_chunks_with_state, schema)

df.createOrReplaceTempView("temp")

df = spark.sql("""
with cte as (
    select
        *,
        case 
            when ema7 > ema20 then 'uptrend' 
            when ema7 < ema20 then 'downtrend' 
            else NULL 
        end as trend,
        abs(close_price - open_price) as body,
        least(open_price, close_price) - low_price as lower_shadow,
        high_price - greatest(open_price, close_price) as upper_shadow
    from temp
)
select
    group_id,
    group_date,
    open_time,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    close_time,
    landing_date,
    symbol,
    ema7,
    ema20,
    trend,
    case 
        when body > 0
            and lower_shadow >= 2 * body
            and upper_shadow <= 0.25 * body
            and trend = 'uptrend'
        then 'hanging man'
        when body > 0
            and lower_shadow >= 2 * body
            and upper_shadow <= 0.25 * body
            and trend = 'downtrend'
        then 'hammer'
        else NULL
    end as pattern
from cte
""")


logger.info(f"Output rows: {df.count()}")


if table_exists(spark, transform_db, pattern_one_table):
    df.writeTo(f"{transform_db}.{pattern_one_table}").overwritePartitions()
else:
    df.writeTo(f"{transform_db}.{pattern_one_table}").tableProperty(
        "format-version", "2"
    ).partitionedBy("symbol", "landing_date").createOrReplace()

logger.info("✅Transform job completed successfully.")
