import logging

from shared_lib.number import round_half_up

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

            for p in pdf["close_price"]:
                price = float(p)

                if state["prev_price"] is None:
                    diff = None
                else:
                    diff = price - state["prev_price"]

                state["prev_price"] = price
                rsi = calc_rsi(diff, state)

                rsi_values.append(round_half_up(rsi, 2) if rsi is not None else None)

            pdf["rsi6"] = rsi_values
            pdf = pdf[[*pdf.columns[:-1], "rsi6"]]
            yield pdf

    logger.info(
        f"Using previous RSI values: prev_price={prev_price}, ag={prev_ag}, al={prev_al}"
    )
    return rsi_in_chunks
