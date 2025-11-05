import logging

from py4j.protocol import Py4JJavaError
from pyspark.errors.exceptions.base import AnalysisException
from pyspark.sql import SparkSession, types

project_prefix = "crypto-cloud-dev-650251698703"
data_lake_bucket_name = "crypto-cloud-dev-650251698703-data-lake-bucket"
data_lake_iceberg_lock_table_name = "crypto_cloud_dev_650251698703_iceberg_lock_table"
data_prefix = project_prefix.replace("-", "_")

landing_date = "2025-09-27"
symbol = "ADAUSDT"

spark = (
    SparkSession.builder.appName("TransformZone Pattern Two")  # type: ignore
    .config(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
        "org.apache.iceberg:iceberg-aws-bundle:1.6.1,"
        "org.apache.hadoop:hadoop-aws:3.3.4",
    )
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config(
        "spark.sql.catalog.glue_catalog.catalog-impl",
        "org.apache.iceberg.aws.glue.GlueCatalog",
    )
    .config(
        "spark.sql.catalog.glue_catalog.warehouse", f"s3a://{data_lake_bucket_name}/"
    )
    .config(
        "spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO"
    )
    .config(
        "spark.sql.catalog.glue_catalog.lock.table",
        f"{data_lake_iceberg_lock_table_name}",
    )
    .config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .config("spark.sql.defaultCatalog", "glue_catalog")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def table_exists(spark: SparkSession, database: str, table: str) -> bool:
    try:
        spark.catalog.getTable(f"{database}.{table}")
        return True
    except (AnalysisException, Py4JJavaError):
        return False


def round_half_up(x, decimals=2):
    if x is None:
        return None
    factor = 10**decimals
    return float(int(x * factor + 0.5)) / factor


def calc_ema(value, state):
    if value is None:
        return None
    prev, buffer, period, k = (
        state["prev"],
        state["buffer"],
        state["period"],
        state["k"],
    )
    if prev is None:
        buffer.append(value)
        if len(buffer) == period:
            ema = sum(buffer) / len(buffer)
        else:
            ema = None
    else:
        ema = (value - prev) * k + prev

    state["prev"] = ema
    return ema


def make_ema_in_chunks(prev_ema7, prev_ema20):
    def ema_in_chunks(iterator):
        ema_configs = {
            "ema7": {
                "period": 7,
                "k": 2 / (7 + 1),
                "prev": prev_ema7,
                "buffer": [],
            },
            "ema20": {
                "period": 20,
                "k": 2 / (20 + 1),
                "prev": prev_ema20,
                "buffer": [],
            },
        }

        for pdf in iterator:
            ema7, ema20 = [], []
            for p in pdf["close_price"]:
                price = float(p)
                e7 = calc_ema(price, ema_configs["ema7"])
                ema7.append(round_half_up(e7, 4) if e7 is not None else None)
                e20 = calc_ema(price, ema_configs["ema20"])
                ema20.append(round_half_up(e20, 4) if e20 is not None else None)

            pdf["ema7"] = ema7
            pdf["ema20"] = ema20
            pdf = pdf[[*pdf.columns[:-2], "ema7", "ema20"]]
            yield pdf

    logger.info(f"Using previous EMA values: ema7={prev_ema7}, ema20={prev_ema20}")
    return ema_in_chunks


logger.info(f"Transforming symbol={symbol} for date={landing_date}")


serving_db = f"{data_prefix}_serving_db"
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


pattern_two_table = "pattern_two"
if table_exists(spark, serving_db, pattern_two_table):
    sql_stmt = f"""
    select ema7, ema20 from {serving_db}.{pattern_two_table}
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
        LAG(open_price, 1) over(order by group_id) as open_price_prev,
        LAG(close_price, 1) over(order by group_id) as close_price_prev
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
        when close_price_prev < open_price_prev
            and close_price > open_price
            and open_price < close_price_prev
            and close_price > open_price_prev
            and trend = 'downtrend'
        then 'bullish engulfing'
        when close_price_prev > open_price_prev
            and close_price < open_price
            and open_price > close_price_prev
            and close_price < open_price_prev
            and trend = 'uptrend'
        then 'bearish engulfing'
        else NULL
    end as pattern
from cte
""")

logger.info(f"Output rows: {df.count()}")


if table_exists(spark, serving_db, pattern_two_table):
    df.writeTo(f"{serving_db}.{pattern_two_table}").overwritePartitions()
else:
    df.writeTo(f"{serving_db}.{pattern_two_table}").tableProperty(
        "format-version", "2"
    ).partitionedBy("symbol", "landing_date").createOrReplace()

logger.info("✅Transform job completed successfully.")
