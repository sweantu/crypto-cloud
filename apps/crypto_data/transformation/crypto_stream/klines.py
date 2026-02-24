from pyflink.table import StreamTableEnvironment
from pyflink.table.statement_set import StatementSet


def create_klines_sink(t_env: StreamTableEnvironment, table_name: str, config: str):
    t_env.execute_sql(f"DROP TABLE IF EXISTS {table_name}")
    t_env.execute_sql(f"""
    CREATE TABLE {table_name} (
        window_start TIMESTAMP_LTZ(3),
        window_end TIMESTAMP_LTZ(3),
        symbol STRING,
        landing_date DATE,
        open_price  DECIMAL(10,6),
        high_price  DECIMAL(10,6),
        low_price   DECIMAL(10,6),
        close_price DECIMAL(10,6),
        volume      DECIMAL(18,8)
    ) 
    WITH {config}
    """)


def create_klines_view(
    t_env: StreamTableEnvironment,
    view_name: str,
    aggtrades_source: str,
):
    t_env.execute_sql(f"DROP TEMPORARY VIEW IF EXISTS {view_name}")
    t_env.execute_sql(f"""
    CREATE TEMPORARY VIEW {view_name} AS
    SELECT
        window_start,
        window_end,
        symbol,
        CAST(window_start AS DATE) AS landing_date,
        ROUND(FIRST_VALUE(price), 6) AS open_price,
        ROUND(MAX(price), 6) AS high_price,
        ROUND(MIN(price), 6) AS low_price,
        ROUND(LAST_VALUE(price), 6) AS close_price,
        ROUND(SUM(quantity), 8) AS volume
    FROM TABLE(
        TUMBLE(TABLE {aggtrades_source}, DESCRIPTOR(ts), INTERVAL '15' MINUTES)
    )
    GROUP BY window_start, window_end, symbol
    """)


def insert_klines(statement_set: StatementSet, klines_sink: str, klines_view: str):
    statement_set.add_insert_sql(
        f"INSERT INTO {klines_sink} SELECT * FROM {klines_view}"
    )
