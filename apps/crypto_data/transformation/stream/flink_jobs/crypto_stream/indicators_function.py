import pickle

from pyflink.common import Row
from pyflink.common.typeinfo import Types
from pyflink.datastream.functions import KeyedProcessFunction
from pyflink.datastream.state import ValueStateDescriptor
from shared_lib.engines import EmaEngine, PatternEngine, RsiEngine
from shared_lib.indicators import detect_trend


class IndicatorsFunction(KeyedProcessFunction):
    def open(self, ctx):
        self.state = ctx.get_state(
            ValueStateDescriptor("indicator_state", Types.PICKLED_BYTE_ARRAY())
        )

    def process_element(self, value, ctx):
        prev_state = pickle.loads(self.state.value()) if self.state.value() else {}

        prev_candle = prev_state.get("prev_candle")
        prev_prev_candle = prev_state.get("prev_prev_candle")

        # --- engines ---
        ema_engine = EmaEngine(prev_state)
        rsi_engine = RsiEngine(prev_state)
        pattern_engine = PatternEngine()

        price = value["close_price"]

        ema_res = ema_engine.update(price)
        rsi6 = rsi_engine.update(price)

        trend = detect_trend(ema_res["ema7"], ema_res["ema20"])
        pattern = pattern_engine.detect(
            c1=prev_prev_candle,
            c2=prev_candle,
            c3=value.as_dict(),
            trend=trend,
        )

        # --- persist state ---
        new_state = {
            **ema_engine.snapshot(),
            **rsi_engine.snapshot(),
            "prev_prev_candle": prev_candle,
            "prev_candle": value.as_dict(),
        }
        self.state.update(pickle.dumps(new_state))

        # --- emit ---
        yield Row(
            **value.as_dict(),
            rsi6=rsi6,
            rsi_ag=new_state["rsi_ag"],
            rsi_al=new_state["rsi_al"],
            ema7=ema_res["ema7"],
            ema20=ema_res["ema20"],
            ema12=ema_res["ema12"],
            ema26=ema_res["ema26"],
            macd=ema_res["macd"],
            signal=ema_res["signal"],
            histogram=ema_res["histogram"],
            trend=trend,
            pattern=pattern,
        )
