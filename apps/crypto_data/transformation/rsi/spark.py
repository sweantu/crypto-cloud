import logging

from common.rsi import Rsi
from pyspark.sql import types
from shared_lib.number import round_half_up
from shared_lib.spark import table_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_rsi_data(
    spark, transform_db, symbol, landing_date, klines_table, rsi_table
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

    if table_exists(spark, transform_db, rsi_table):
        sql_stmt = f"""
        SELECT
            close_price AS prev_price,
            rsi_ag      AS prev_ag,
            rsi_al      AS prev_al
        FROM {transform_db}.{rsi_table}
        WHERE landing_date = date_sub(DATE('{landing_date}'), 1)
        AND symbol = '{symbol}'
        ORDER BY group_id DESC
        LIMIT 1
        """
        row = spark.sql(sql_stmt).first()

        if row:
            prev_price = row["prev_price"]
            prev_ag = row["prev_ag"]
            prev_al = row["prev_al"]
        else:
            prev_price = prev_ag = prev_al = None
    else:
        prev_price = prev_ag = prev_al = None

    rsi_in_chunks_with_state = make_rsi_in_chunks(
        prev_price=prev_price,
        prev_ag=prev_ag,
        prev_al=prev_al,
    )

    schema = types.StructType(
        [
            *df_sorted.schema.fields,  # keep all original fields
            types.StructField("rsi6", types.DoubleType(), True),
            types.StructField("rsi_ag", types.DoubleType(), True),
            types.StructField("rsi_al", types.DoubleType(), True),
        ]
    )

    df = df_sorted.mapInPandas(rsi_in_chunks_with_state, schema)

    if table_exists(spark, transform_db, rsi_table):
        df.writeTo(f"{transform_db}.{rsi_table}").overwritePartitions()
    else:
        df.writeTo(f"{transform_db}.{rsi_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy("symbol", "landing_date").createOrReplace()


def make_rsi_in_chunks(prev_price=None, prev_ag=None, prev_al=None):
    def rsi_in_chunks(iterator):
        rsi_state = Rsi(period=6, prev=prev_price, prev_ag=prev_ag, prev_al=prev_al)

        for pdf in iterator:
            rsi_values = []
            rsi_ag = []
            rsi_al = []

            for p in pdf["close_price"]:
                price = float(p)

                rsi = rsi_state.calculate(price)
                ag = rsi_state.prev_ag
                al = rsi_state.prev_al
                rsi_values.append(round_half_up(rsi, 2) if rsi is not None else None)
                rsi_ag.append(round_half_up(ag, 6) if ag is not None else None)
                rsi_al.append(round_half_up(al, 6) if al is not None else None)

            pdf["rsi6"] = rsi_values
            pdf["rsi_ag"] = rsi_ag
            pdf["rsi_al"] = rsi_al
            pdf = pdf[[*pdf.columns[:-3], "rsi6", "rsi_ag", "rsi_al"]]
            yield pdf

    logger.info(
        f"Using previous RSI values: prev_price={prev_price}, ag={prev_ag}, al={prev_al}"
    )
    return rsi_in_chunks
