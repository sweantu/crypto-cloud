import logging

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_signal_outcomes_data(
    spark: SparkSession,
    date,
    transform_db,
    klines_table,
    signals_table,
    signal_outcomes_table,
):
    outcomes_df = spark.sql(f"""
    with future_klines as (
      select 
        symbol, 
        interval, 
        open_time, 
        lead(close_price, 5) over (partition by symbol, interval order by open_time) as close_5,
        lead(open_time, 5) over (partition by symbol, interval order by open_time) as exit_time_5,
        lead(close_price, 15) over (partition by symbol, interval order by open_time) as close_15,
        lead(open_time, 15) over (partition by symbol, interval order by open_time) as exit_time_15,
        lead(close_price, 30) over (partition by symbol, interval order by open_time) as close_30,
        lead(open_time, 30) over (partition by symbol, interval order by open_time) as exit_time_30
      from {transform_db}.{klines_table}
      where date >= '{date}' and date <= cast(date_add(to_date('{date}'), 40) as string)
    )
    , exploded as (
      select 
        s.signal_id,
        s.date,
        s.signal_direction,
        s.entry_price,
        h.horizon,
        case 
          when h.horizon = 5 then f.exit_time_5
          when h.horizon = 15 then f.exit_time_15
          when h.horizon = 30 then f.exit_time_30
        end as exit_time,
        case 
          when h.horizon = 5 then f.close_5
          when h.horizon = 15 then f.close_15
          when h.horizon = 30 then f.close_30
        end as exit_price
      from {transform_db}.{signals_table} s
      join future_klines f on s.symbol = f.symbol and s.interval = f.interval and s.signal_time = f.open_time
      cross join (
        select explode(array(5, 15, 30)) as horizon
      ) h
      where s.date = '{date}'
    )
    select 
      signal_id,
      horizon,
      exit_time,
      entry_price,
      exit_price,
      (exit_price - entry_price) / entry_price as return_pct,
      case
        when exit_price is null then null
        when signal_direction = 'bullish' and ((exit_price - entry_price) / entry_price) > 0 then true
        when signal_direction = 'bearish' and ((exit_price - entry_price) / entry_price) < 0 then true
        else false
      end as is_win,
      date
    from exploded
    """)

    outcomes_df = outcomes_df.repartition("horizon", "date")

    if table_exists(spark, transform_db, signal_outcomes_table):
        outcomes_df.writeTo(f"{transform_db}.{signal_outcomes_table}").overwritePartitions()
        logger.info(f"Table {transform_db}.{signal_outcomes_table} overwritten for {date}")
    else:
        outcomes_df.writeTo(f"{transform_db}.{signal_outcomes_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy(F.col("date")).createOrReplace()
        logger.info(f"Table {transform_db}.{signal_outcomes_table} created for {date}")
