import logging

from common.ema import Ema
from pyspark.sql import types
from shared_lib.number import round_half_up
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_macd_in_chunks(
    prev_ema12=None,
    prev_ema26=None,
    prev_signal=None,
):
    def macd_in_chunks(iterator):

        ema12_state = Ema(period=12, prev=prev_ema12)
        ema26_state = Ema(period=26, prev=prev_ema26)
        signal_state = Ema(period=9, prev=prev_signal)

        for pdf in iterator:
            ema12_vals = []
            ema26_vals = []
            macd_vals = []
            signal_vals = []
            hist_vals = []

            for p in pdf["close_price"]:
                price = float(p)

                e12 = ema12_state.calculate(price)
                e26 = ema26_state.calculate(price)

                ema12_vals.append(round_half_up(e12, 2) if e12 is not None else None)
                ema26_vals.append(round_half_up(e26, 2) if e26 is not None else None)

                macd = e12 - e26 if e12 is not None and e26 is not None else None
                macd_vals.append(round_half_up(macd, 2) if macd is not None else None)

                signal = signal_state.calculate(macd) if macd is not None else None
                signal_vals.append(
                    round_half_up(signal, 2) if signal is not None else None
                )

                hist = (
                    macd - signal if macd is not None and signal is not None else None
                )
                hist_vals.append(round_half_up(hist, 2) if hist is not None else None)

            pdf["ema12"] = ema12_vals
            pdf["ema26"] = ema26_vals
            pdf["macd"] = macd_vals
            pdf["signal"] = signal_vals
            pdf["histogram"] = hist_vals

            pdf = pdf[
                [*pdf.columns[:-5], "ema12", "ema26", "macd", "signal", "histogram"]
            ]
            yield pdf

    logger.info(
        f"Using previous MACD state: ema12={prev_ema12}, ema26={prev_ema26}, signal={prev_signal}"
    )
    return macd_in_chunks


def process_macd_data(
    spark, transform_db, symbol, landing_date, klines_table, macd_table
):
    sql_stmt = f"""
    select * from {transform_db}.{klines_table}
    where landing_date = DATE('{landing_date}') AND symbol = '{symbol}'
    """
    df_sorted = (
        spark.sql(sql_stmt)
        .coalesce(1)  # one partition, not shuffle
        .sortWithinPartitions("group_id")
    )

    if table_exists(spark, transform_db, macd_table):
        sql_stmt = f"""
        SELECT
            ema12      AS macd_ema12,
            ema26      AS macd_ema26,
            signal     AS macd_signal
        FROM {transform_db}.{macd_table}
        WHERE landing_date = date_sub(DATE('{landing_date}'), 1)
        AND symbol = '{symbol}'
        ORDER BY group_id DESC
        LIMIT 1
        """
        row = spark.sql(sql_stmt).first()

        if row:
            prev_ema12 = row["macd_ema12"]
            prev_ema26 = row["macd_ema26"]
            prev_signal = row["macd_signal"]
        else:
            prev_ema12 = prev_ema26 = prev_signal = None
    else:
        prev_ema12 = prev_ema26 = prev_signal = None

    macd_in_chunks_with_state = make_macd_in_chunks(
        prev_ema12=prev_ema12,
        prev_ema26=prev_ema26,
        prev_signal=prev_signal,
    )

    schema = types.StructType(
        [
            *df_sorted.schema.fields,  # keep all original fields
            types.StructField("ema12", types.DoubleType(), True),
            types.StructField("ema26", types.DoubleType(), True),
            types.StructField("macd", types.DoubleType(), True),
            types.StructField("signal", types.DoubleType(), True),
            types.StructField("histogram", types.DoubleType(), True),
        ]
    )

    df = df_sorted.mapInPandas(macd_in_chunks_with_state, schema)

    if table_exists(spark, transform_db, macd_table):
        df.writeTo(f"{transform_db}.{macd_table}").overwritePartitions()
    else:
        (
            df.writeTo(f"{transform_db}.{macd_table}")
            .tableProperty("format-version", "2")
            .partitionedBy("symbol", "landing_date")
            .createOrReplace()
        )
