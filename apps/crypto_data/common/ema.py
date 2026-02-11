import copy
import logging

from shared_lib.number import round_half_up

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_ema_in_chunks(prev_ema7, prev_ema20):
    def ema_in_chunks(iterator):
        ema_configs = {
            "ema7": {
                "period": 7,
                "k": 2 / (7 + 1),
                "prev": prev_ema7,
                "buffer": [],
            },
            "ema20": {
                "period": 20,
                "k": 2 / (20 + 1),
                "prev": prev_ema20,
                "buffer": [],
            },
        }

        for pdf in iterator:
            ema7, ema20 = [], []
            for p in pdf["close_price"]:
                price = float(p)
                e7 = calc_ema(price, ema_configs["ema7"])
                ema7.append(round_half_up(e7, 4) if e7 is not None else None)
                e20 = calc_ema(price, ema_configs["ema20"])
                ema20.append(round_half_up(e20, 4) if e20 is not None else None)

            pdf["ema7"] = ema7
            pdf["ema20"] = ema20
            pdf = pdf[[*pdf.columns[:-2], "ema7", "ema20"]]
            yield pdf

    logger.info(f"Using previous EMA values: ema7={prev_ema7}, ema20={prev_ema20}")
    return ema_in_chunks

def calc_ema(value, state):
    if value is None:
        return None
    prev, buffer, period, k = (
        state["prev"],
        state["buffer"],
        state["period"],
        state["k"],
    )
    if prev is None:
        buffer.append(value)
        if len(buffer) == period:
            ema = sum(buffer) / len(buffer)
            buffer.clear()
        else:
            ema = None
    else:
        ema = (value - prev) * k + prev

    state["prev"] = ema
    return ema


def detect_trend(ema7, ema20):
    if ema7 is None or ema20 is None:
        return None
    if ema7 > ema20:
        return "uptrend"
    elif ema7 < ema20:
        return "downtrend"
    return None


class EmaEngine:
    def __init__(self, prev_state: dict):
        self.configs = {
            "ema7": self._cfg(7, prev_state, "ema7", "buffer7_state"),
            "ema20": self._cfg(20, prev_state, "ema20", "buffer20_state"),
            "ema12": self._cfg(12, prev_state, "ema12", "buffer12_state"),
            "ema26": self._cfg(26, prev_state, "ema26", "buffer26_state"),
            "signal": self._cfg(9, prev_state, "signal", "buffer_signal_state"),
        }

    def _cfg(self, period, state, key, buf_key):
        return {
            "period": period,
            "k": 2 / (period + 1),
            "prev": state.get(key),
            "buffer": copy.deepcopy(state.get(buf_key, [])),
        }

    def update(self, price):
        ema7 = calc_ema(price, self.configs["ema7"])
        ema20 = calc_ema(price, self.configs["ema20"])
        ema12 = calc_ema(price, self.configs["ema12"])
        ema26 = calc_ema(price, self.configs["ema26"])

        macd = ema12 - ema26 if ema12 is not None and ema26 is not None else None
        signal = calc_ema(macd, self.configs["signal"])
        hist = macd - signal if macd is not None and signal is not None else None

        return {
            "ema7": ema7,
            "ema20": ema20,
            "ema12": ema12,
            "ema26": ema26,
            "macd": macd,
            "signal": signal,
            "histogram": hist,
        }

    def snapshot(self):
        return {
            "ema7": self.configs["ema7"]["prev"],
            "ema20": self.configs["ema20"]["prev"],
            "ema12": self.configs["ema12"]["prev"],
            "ema26": self.configs["ema26"]["prev"],
            "signal": self.configs["signal"]["prev"],
            "buffer7_state": self.configs["ema7"]["buffer"],
            "buffer20_state": self.configs["ema20"]["buffer"],
            "buffer12_state": self.configs["ema12"]["buffer"],
            "buffer26_state": self.configs["ema26"]["buffer"],
            "buffer_signal_state": self.configs["signal"]["buffer"],
        }