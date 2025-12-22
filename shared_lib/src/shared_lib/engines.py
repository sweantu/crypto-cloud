import copy

from .indicators import (
    calc_ema,
    calc_rsi,
    detect_pattern_one,
    detect_pattern_three,
    detect_pattern_two,
)

# ===================== EMA ENGINE =====================


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


# ===================== RSI ENGINE =====================


class RsiEngine:
    def __init__(self, prev_state: dict):
        self.state = {
            "period": 6,
            "buffer": copy.deepcopy(prev_state.get("buffer_rsi_state", [])),
            "ag": prev_state.get("rsi_ag"),
            "al": prev_state.get("rsi_al"),
            "initialized": prev_state.get("rsi_ag") is not None
            and prev_state.get("rsi_al") is not None,
            "prev_price": prev_state.get("close_price"),
        }

    def update(self, close_price):
        prev_price = self.state["prev_price"]
        diff = close_price - prev_price if prev_price is not None else None
        self.state["prev_price"] = close_price
        return calc_rsi(diff, self.state)

    def snapshot(self):
        return {
            "buffer_rsi_state": self.state["buffer"],
            "rsi_ag": self.state["ag"],
            "rsi_al": self.state["al"],
        }


# ===================== PATTERN ENGINE =====================


class PatternEngine:
    def detect(self, c1, c2, c3, trend):
        """
        Priority:
        1. Three-candle patterns
        2. Two-candle patterns
        3. One-candle patterns
        """

        return (
            detect_pattern_three(c1, c2, c3, trend)
            or detect_pattern_two(c3, c2, trend)
            or detect_pattern_one(c3, trend)
        )
