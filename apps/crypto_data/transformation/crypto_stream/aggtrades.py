from pyflink.table import StreamTableEnvironment


def create_aggtrades_source(
    t_env: StreamTableEnvironment, table_name: str, config: str
):
    t_env.execute_sql(f"DROP TABLE IF EXISTS {table_name}")
    t_env.execute_sql(f"""
    CREATE TABLE {table_name} (
        agg_trade_id BIGINT,
        price DOUBLE,
        quantity DOUBLE,
        first_trade_id BIGINT,
        last_trade_id BIGINT,
        ts_int BIGINT,
        is_buyer_maker BOOLEAN,
        is_best_match BOOLEAN,
        symbol STRING,
        ts AS TO_TIMESTAMP_LTZ(ts_int / 1000, 3),
        WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
    ) 
    WITH {config}
    """)
