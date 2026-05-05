import logging

from common.ema import Ema
from common.rsi import Rsi
from pyspark.sql import SparkSession, types
from pyspark.sql import functions as F
from shared_lib.number import round_half_up
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_kline_features_data(
    spark: SparkSession,
    date,
    transform_db,
    klines_table,
    kline_features_table,
):
    kline_df = spark.sql(f"""
    select symbol, open_time, interval, open_price, high_price, low_price, close_price, date from {transform_db}.{klines_table} where date = '{date}'
    """)

    kline_features_df = kline_df.repartition("symbol", "interval").sortWithinPartitions(
        "open_time"
    )

    kline_features_df = add_indicators(kline_features_df)
    kline_features_df = add_vol(spark, kline_features_df)
    kline_features_df = add_patterns(spark, kline_features_df)

    if table_exists(spark, transform_db, kline_features_table):
        kline_features_df.writeTo(
            f"{transform_db}.{kline_features_table}"
        ).overwritePartitions()
        logger.info(
            f"Table {transform_db}.{kline_features_table} overwritten for {date}"
        )
    else:
        kline_features_df.writeTo(
            f"{transform_db}.{kline_features_table}"
        ).tableProperty("format-version", "2").partitionedBy(
            F.col("date")
        ).createOrReplace()
        logger.info(f"Table {transform_db}.{kline_features_table} created for {date}")


def add_indicators(kline_features_df):
    def chunks(iterator):
        state = {}
        for pdf in iterator:
            ema7_list = []
            ema20_list = []
            rsi6_list = []
            macd_list = []
            signal_list = []
            hist_list = []
            for _, row in pdf.iterrows():
                key = f"symbol::{row['symbol']}::interval::{row['interval']}"
                if key not in state:
                    state[key] = {
                        "ema7_state": Ema(period=7),
                        "ema20_state": Ema(period=20),
                        "rsi6_state": Rsi(period=6),
                        "ema12_state": Ema(period=12),
                        "ema26_state": Ema(period=26),
                        "signal_state": Ema(period=9),
                    }
                price = float(row["close_price"])

                ema7 = state[key]["ema7_state"].calculate(price)
                ema20 = state[key]["ema20_state"].calculate(price)
                ema7_list.append(round_half_up(ema7, 4) if ema7 is not None else None)
                ema20_list.append(
                    round_half_up(ema20, 4) if ema20 is not None else None
                )

                rsi = state[key]["rsi6_state"].calculate(price)
                rsi6_list.append(round_half_up(rsi, 2) if rsi is not None else None)

                ema12 = state[key]["ema12_state"].calculate(price)
                ema26 = state[key]["ema26_state"].calculate(price)
                macd = (
                    ema12 - ema26 if ema12 is not None and ema26 is not None else None
                )
                signal = (
                    state[key]["signal_state"].calculate(macd)
                    if macd is not None
                    else None
                )
                hist = (
                    macd - signal if macd is not None and signal is not None else None
                )

                macd_list.append(round_half_up(macd, 8) if macd is not None else None)
                signal_list.append(
                    round_half_up(signal, 8) if signal is not None else None
                )
                hist_list.append(round_half_up(hist, 8) if hist is not None else None)

            pdf["ema7"] = ema7_list
            pdf["ema20"] = ema20_list
            pdf["rsi6"] = rsi6_list
            pdf["macd"] = macd_list
            pdf["signal"] = signal_list
            pdf["hist"] = hist_list
            yield pdf

    schema = types.StructType(
        [
            *kline_features_df.schema.fields,
            types.StructField("ema7", types.DoubleType(), True),
            types.StructField("ema20", types.DoubleType(), True),
            types.StructField("rsi6", types.DoubleType(), True),
            types.StructField("macd", types.DoubleType(), True),
            types.StructField("signal", types.DoubleType(), True),
            types.StructField("hist", types.DoubleType(), True),
        ]
    )
    return kline_features_df.mapInPandas(chunks, schema=schema)


def add_vol(spark, kline_features_df):
    kline_features_df.createOrReplaceTempView("kline_features")
    return spark.sql("""
    with base as (
        select 
            *, 
            lag(close_price) over (partition by symbol, interval order by open_time) as close_price_prev,
            lag(open_price) over (partition by symbol, interval order by open_time) as open_price_prev
        from kline_features
    )
    , returns as (
        select
            *,
            close_price / close_price_prev as log_return
        from base
    )
    select 
    symbol, open_time, interval, date, open_price, high_price, low_price, close_price, close_price_prev, open_price_prev, ema7, ema20, rsi6, macd, signal, hist,
    round(stddev(log_return) over (partition by symbol, interval order by open_time rows between 19 preceding and current row), 4) as rolling_vol_20
    from returns
    """)


def add_patterns(spark, kline_features_df):
    kline_features_df.createOrReplaceTempView("kline_features")
    return spark.sql("""
    with base as (
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
        from kline_features
    )
    select 
        symbol, open_time, interval, date, open_price, high_price, low_price, close_price, ema7, ema20, rsi6, macd, signal, hist, rolling_vol_20,
        case
            when body > 0
                and lower_shadow >= 2 * body
                and upper_shadow <= 0.25 * body
                and trend = 'downtrend'
            then true
            else false
        end as pattern_hammer,
        case 
            when close_price_prev < open_price_prev
                and close_price > open_price
                and open_price < close_price_prev
                and close_price > open_price_prev
                and trend = 'downtrend'
            then true
            else false
        end as pattern_bullish_engulfing,
        case
            when close_price_prev > open_price_prev
                and close_price < open_price
                and open_price > close_price_prev
                and close_price < open_price_prev
                and trend = 'uptrend'
            then true
            else false
        end as pattern_bearish_engulfing
    from base
    """)
