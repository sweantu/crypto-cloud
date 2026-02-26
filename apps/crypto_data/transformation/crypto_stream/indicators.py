import pickle

from common.ema import Ema, detect_trend
from common.pattern import detectPattern
from common.rsi import Rsi
from pyflink.common import Row, Types
from pyflink.datastream.functions import KeyedProcessFunction
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.table import StreamTableEnvironment
from pyflink.table.statement_set import StatementSet


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
    statement_set: StatementSet, indicators_sink_table: str, indicators_view: str
):
    statement_set.add_insert_sql(
        f"INSERT INTO {indicators_sink_table} SELECT * FROM {indicators_view}"
    )


def insert_indicators_stream(
    statement_set: StatementSet, indicators_sink_table: str, indicators_view: str
):
    statement_set.add_insert_sql(
        f"INSERT INTO {indicators_sink_table} SELECT * FROM {indicators_view} where `pattern` IS NOT NULL"
    )


class IndicatorsFunction(KeyedProcessFunction):
    def open(self, ctx):
        self.state = ctx.get_state(
            ValueStateDescriptor("indicator_state", Types.PICKLED_BYTE_ARRAY())
        )

    def process_element(self, value, ctx):
        prev_state = (
            pickle.loads(self.state.value())
            if self.state.value()
            else {
                "ema7": Ema(period=7),
                "ema20": Ema(period=20),
                "ema12": Ema(period=12),
                "ema26": Ema(period=26),
                "signal": Ema(period=9),
                "rsi6": Rsi(period=6),
                "prev_kline": None,
                "prev_prev_kline": None,
            }
        )

        curr_kline = value.as_dict()
        close_price = curr_kline["close_price"]

        ema7 = prev_state["ema7"].calculate(close_price)
        ema20 = prev_state["ema20"].calculate(close_price)
        ema12 = prev_state["ema12"].calculate(close_price)
        ema26 = prev_state["ema26"].calculate(close_price)

        macd = ema12 - ema26 if ema12 is not None and ema26 is not None else None
        signal = prev_state["signal"].calculate(macd) if macd is not None else None
        histogram = macd - signal if macd is not None and signal is not None else None

        rsi6 = prev_state["rsi6"].calculate(close_price)

        trend = detect_trend(ema7, ema20)
        pattern = detectPattern(
            c1=prev_state["prev_prev_kline"],
            c2=prev_state["prev_kline"],
            c3=curr_kline,
            trend=trend,
        )

        # --- persist state ---
        new_state = {
            "ema7": prev_state["ema7"],
            "ema20": prev_state["ema20"],
            "ema12": prev_state["ema12"],
            "ema26": prev_state["ema26"],
            "signal": prev_state["signal"],
            "rsi6": prev_state["rsi6"],
            "prev_prev_kline": prev_state["prev_kline"],
            "prev_kline": curr_kline,
        }
        self.state.update(pickle.dumps(new_state))

        # --- emit ---
        yield Row(
            **curr_kline,
            rsi_al=prev_state["rsi6"].prev_al,
            rsi_ag=prev_state["rsi6"].prev_ag,
            rsi6=rsi6,
            ema7=ema7,
            ema20=ema20,
            ema12=ema12,
            ema26=ema26,
            macd=macd,
            signal=signal,
            histogram=histogram,
            trend=trend,
            pattern=pattern,
        )
