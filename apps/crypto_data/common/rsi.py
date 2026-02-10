import logging

from shared_lib.indicators import calc_rsi
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
