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
