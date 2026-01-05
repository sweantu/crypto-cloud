import logging

from shared_lib.indicators import calc_ema
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
