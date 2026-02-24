from pyflink.common import Types
from pyflink.table import StreamTableEnvironment
from pyflink.table.statement_set import StatementSet

from .indicators_function import IndicatorsFunction


def create_indicators_sink(t_env: StreamTableEnvironment, table_name: str, config: str):
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
        volume      DECIMAL(18,8),
                      
        rsi6   DECIMAL(5,2),
        rsi_ag DECIMAL(18,8),
        rsi_al DECIMAL(18,8),
                      
        ema7  DECIMAL(10,6),
        ema20 DECIMAL(10,6),
        ema12 DECIMAL(10,6),
        ema26 DECIMAL(10,6),
                      
        macd      DECIMAL(18,8),
        signal    DECIMAL(18,8),
        histogram DECIMAL(18,8),
                      
        trend STRING,
        `pattern` STRING
    ) 
    WITH {config}
    """)


def create_indicator_view(
    t_env: StreamTableEnvironment, view_name: str, klines_view: str
):
    typeinfo = Types.ROW_NAMED(
        [
            "window_start",
            "window_end",
            "symbol",
            "landing_date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
            "rsi6",
            "rsi_ag",
            "rsi_al",
            "ema7",
            "ema20",
            "ema12",
            "ema26",
            "macd",
            "signal",
            "histogram",
            "trend",
            "pattern",
        ],
        [
            Types.SQL_TIMESTAMP(),
            Types.SQL_TIMESTAMP(),
            Types.STRING(),
            Types.SQL_DATE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.DOUBLE(),
            Types.STRING(),
            Types.STRING(),
        ],
    )

    klines_stream = t_env.to_data_stream(t_env.from_path(f"{klines_view}"))
    indicators_stream = klines_stream.key_by(lambda x: x["symbol"]).process(
        IndicatorsFunction(), output_type=typeinfo
    )
    t_env.drop_temporary_view(f"{view_name}")
    t_env.create_temporary_view(
        f"{view_name}", t_env.from_data_stream(indicators_stream)
    )


def insert_indicators_clickhouse(
    statement_set: StatementSet, indicators_sink: str, indicators_view: str
):
    statement_set.add_insert_sql(
        f"INSERT INTO {indicators_sink} SELECT * FROM {indicators_view}"
    )


def insert_indicators_kafka(
    statement_set: StatementSet, indicators_sink: str, indicators_view: str
):
    statement_set.add_insert_sql(
        f"INSERT INTO {indicators_sink} SELECT * FROM {indicators_view} where `pattern` IS NOT NULL"
    )
