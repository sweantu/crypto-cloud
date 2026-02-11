import copy
import logging

from shared_lib.number import round_half_up

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_rsi_in_chunks(prev_price=None, prev_ag=None, prev_al=None):
    def rsi_in_chunks(iterator):
        state = {
            "period": 6,
            "buffer": [],
            "ag": prev_ag,
            "al": prev_al,
            "initialized": prev_ag is not None and prev_al is not None,
            "prev_price": prev_price,
        }

        for pdf in iterator:
            rsi_values = []
            rsi_ag = []
            rsi_al = []

            for p in pdf["close_price"]:
                price = float(p)

                if state["prev_price"] is None:
                    diff = None
                else:
                    diff = price - state["prev_price"]

                state["prev_price"] = price
                rsi = calc_rsi(diff, state)
                ag = state["ag"]
                al = state["al"]
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


def calc_rsi(diff, state):
    """
    Wilder RSI calculation (EMA-style state)
    """
    if diff is None:
        return None

    period = state["period"]
    buffer = state["buffer"]
    ag = state["ag"]
    al = state["al"]
    initialized = state["initialized"]

    if not initialized:
        buffer.append(diff)

        if len(buffer) < period:
            return None

        ag = sum(d for d in buffer if d > 0) / period
        al = sum(-d for d in buffer if d < 0) / period
        state["initialized"] = True
    else:
        ag = ((ag * (period - 1)) + (diff if diff > 0 else 0.0)) / period
        al = ((al * (period - 1)) + (-diff if diff < 0 else 0.0)) / period

    state["ag"] = ag
    state["al"] = al

    if al == 0:
        rsi = 100.0
    elif ag == 0:
        rsi = 0.0
    else:
        rs = ag / al
        rsi = 100.0 - (100.0 / (1.0 + rs))

    return rsi


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
        result = calc_rsi(diff, self.state)
        return result

    def snapshot(self):
        return {
            "buffer_rsi_state": self.state["buffer"],
            "rsi_ag": self.state["ag"],
            "rsi_al": self.state["al"],
            "close_price": self.state["prev_price"],
        }