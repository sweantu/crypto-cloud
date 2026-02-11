from common.rsi import make_rsi_in_chunks
from pyspark.sql import types
from shared_lib.spark import table_exists


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
        (
            df.writeTo(f"{transform_db}.{rsi_table}")
            .tableProperty("format-version", "2")
            .partitionedBy("symbol", "landing_date")
            .createOrReplace()
        )
