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
        "project_prefix_underscore",
        "data_lake_bucket",
        "iceberg_lock_table",
    ],
)

# parser = argparse.ArgumentParser()
# parser.add_argument("--symbol", required=True)
# parser.add_argument("--landing_date", required=True)
# parser.add_argument("--project_prefix_underscore", required=True)
# parser.add_argument("--data_lake_bucket", required=True)
# parser.add_argument("--iceberg_lock_table", required=True)
# args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]
logger.info(f"Transforming symbol={symbol} for date={landing_date}")

DATA_LAKE_BUCKET = args["data_lake_bucket"]
ICEBERG_LOCK_TABLE = args["iceberg_lock_table"]
PROJECT_PREFIX_UNDERSCORE = args["project_prefix_underscore"]


spark = (
    SparkSession.builder.appName("TransformZone Pattern Three")  # type: ignore
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


serving_db = f"glue_catalog.{PROJECT_PREFIX_UNDERSCORE}_serving_db"
klines_table = "klines"
sql_stmt = f"""
select * from {serving_db}.{klines_table}
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


pattern_three_table = "pattern_three"
if table_exists(spark, serving_db, pattern_three_table):
    sql_stmt = f"""
    select ema7, ema20 from {serving_db}.{pattern_three_table}
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
        lag(open_price, 2) over(order by group_id) as o1,
        lag(close_price, 2) over(order by group_id) as c1,
        lag(open_price, 1) over(order by group_id) as o2,
        lag(close_price, 1) over(order by group_id) as c2,
        open_price as o3,
        close_price as c3,
        lag(high_price, 1) over(order by group_id) as h2,
        lag(low_price, 1) over(order by group_id) as l2
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
        when c1 < o1
             and abs(c2 - o2) <= 0.5 * abs(o1 - c1)
             and c2 < c1 and o2 < c1
             and c3 > o3
             and c3 >= (o1 + c1)/2
             and trend = 'downtrend'
        then 'morning star'

        when c1 > o1
             and abs(c2 - o2) <= 0.5 * abs(c1 - o1)
             and o2 > c1 and c2 > c1
             and c3 < o3
             and c3 <= (o1 + c1)/2
             and trend = 'uptrend'
        then 'evening star'

        when c1 < o1
             and abs(c2 - o2) <= 0.1 * (h2 - l2)
             and c2 < c1 and o2 < c1
             and c3 > o3
             and c3 >= (o1 + c1)/2
             and trend = 'downtrend'
        then 'morning doji star'

        when c1 > o1
             and abs(c2 - o2) <= 0.1 * (h2 - l2)
             and o2 > c1 and c2 > c1
             and c3 < o3
             and c3 <= (o1 + c1)/2
             and trend = 'uptrend'
        then 'evening doji star'

        else null
    end as pattern
from cte
""")
logger.info(f"Output rows: {df.count()}")


if table_exists(spark, serving_db, pattern_three_table):
    df.writeTo(f"{serving_db}.{pattern_three_table}").overwritePartitions()
else:
    df.writeTo(f"{serving_db}.{pattern_three_table}").tableProperty(
        "format-version", "2"
    ).partitionedBy("symbol", "landing_date").createOrReplace()

logger.info("✅Transform job completed successfully.")
