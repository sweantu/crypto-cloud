from common.ema import make_ema_in_chunks
from common.spark import table_exists
from pyspark.sql import types


def process_pattern_three_data(
    spark, transform_db, symbol, landing_date, klines_table, pattern_three_table
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

    schema = types.StructType(
        [
            *df_sorted.schema.fields,  # keep all original fields
            types.StructField("ema7", types.DoubleType(), True),
            types.StructField("ema20", types.DoubleType(), True),
        ]
    )

    if table_exists(spark, transform_db, pattern_three_table):
        sql_stmt = f"""
        select ema7, ema20 from {transform_db}.{pattern_three_table}
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

    if table_exists(spark, transform_db, pattern_three_table):
        df.writeTo(f"{transform_db}.{pattern_three_table}").overwritePartitions()
    else:
        df.writeTo(f"{transform_db}.{pattern_three_table}").tableProperty(
            "format-version", "2"
        ).partitionedBy("symbol", "landing_date").createOrReplace()
