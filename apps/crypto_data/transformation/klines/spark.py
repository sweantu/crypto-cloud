import logging

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_klines_data(
    spark: SparkSession,
    date,
    transform_db,
    aggtrades_table,
    klines_table,
):
    df_1h = (
        create_klines_df(
            spark, transform_db, aggtrades_table, seconds=60 * 60, date=date
        )
        .withColumn("date", F.lit(date))
        .withColumn("interval", F.lit("1h"))
    )
    df_5m = (
        create_klines_df(
            spark, transform_db, aggtrades_table, seconds=60 * 5, date=date
        )
        .withColumn("date", F.lit(date))
        .withColumn("interval", F.lit("5m"))
    )
    df_15m = (
        create_klines_df(
            spark, transform_db, aggtrades_table, seconds=60 * 15, date=date
        )
        .withColumn("date", F.lit(date))
        .withColumn("interval", F.lit("15m"))
    )
    df = df_1h.unionByName(df_5m).unionByName(df_15m)

    if table_exists(spark, transform_db, klines_table):
        df.writeTo(f"{transform_db}.{klines_table}").overwritePartitions()
        logger.info(f"Table {transform_db}.{klines_table} overwritten for {date}")
    else:
        df.writeTo(f"{transform_db}.{klines_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("date")).createOrReplace()
        logger.info(f"Table {transform_db}.{klines_table} created for {date}")


def create_klines_df(spark, transform_db, aggtrades_table, seconds, date):
    df = spark.sql(f"""
    with base as (
        select 
            *,
            cast(floor(cast(event_time as long) / {seconds}) * {seconds} as timestamp) as open_time
        from {transform_db}.{aggtrades_table} where event_date = '{date}' 
    )
    , base_with_rn as (
        select
            *,
            row_number() over (partition by symbol, open_time order by event_time, agg_trade_id) as rn_open,
            row_number() over (partition by symbol, open_time order by event_time desc, agg_trade_id desc) as rn_close
        from base
    )
    , agg as (
        select
            symbol,
            open_time,
            round(max(price), 4) as high_price,
            round(min(price), 4) as low_price,
            round(sum(quantity), 1) as volume,
            round(sum(notional), 1) as quote_volume,
            count(*) as trade_count,
            round(sum(case when is_buyer_maker = false then quantity else 0 end), 1) as buy_volume,
            round(sum(case when is_buyer_maker = true then quantity else 0 end), 1) as sell_volume,
            round(sum(case when is_buyer_maker = false then notional else 0 end), 1) as buy_notional,
            round(sum(case when is_buyer_maker = true then notional else 0 end), 1) as sell_notional
            from base_with_rn
            group by symbol, open_time
    )
    , open as (
        select
            symbol,
            open_time,
            round(price, 4) as open_price
        from base_with_rn
        where rn_open = 1
    )
    , close as (
        select
            symbol,
            open_time,
            round(price, 4) as close_price
        from base_with_rn
        where rn_close = 1
    )
    select
        agg.symbol,
        agg.open_time,
        open.open_price,
        agg.high_price,
        agg.low_price,
        close.close_price,
        agg.volume,
        agg.quote_volume,
        agg.trade_count,
        agg.buy_volume,
        agg.sell_volume,
        agg.buy_notional,
        agg.sell_notional,
        round((close.close_price - open.open_price) / open.open_price, 4) as return_1

    from agg
    join open on agg.symbol = open.symbol and agg.open_time = open.open_time
    join close on agg.symbol = close.symbol and agg.open_time = close.open_time
    """)
    return df