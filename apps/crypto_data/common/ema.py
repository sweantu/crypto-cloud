import logging

from shared_lib.number import round_half_up

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_ema_in_chunks(prev_ema7, prev_ema20):
    def ema_in_chunks(iterator):

        ema7_state = Ema(period=7, prev=prev_ema7)
        ema20_state = Ema(period=20, prev=prev_ema20)

        for pdf in iterator:
            ema7, ema20 = [], []
            for p in pdf["close_price"]:
                price = float(p)
                e7 = ema7_state.calculate(price)
                ema7.append(round_half_up(e7, 4) if e7 is not None else None)
                e20 = ema20_state.calculate(price)
                ema20.append(round_half_up(e20, 4) if e20 is not None else None)

            pdf["ema7"] = ema7
            pdf["ema20"] = ema20
            pdf = pdf[[*pdf.columns[:-2], "ema7", "ema20"]]
            yield pdf

    logger.info(f"Using previous EMA values: ema7={prev_ema7}, ema20={prev_ema20}")
    return ema_in_chunks


def detect_trend(ema7, ema20):
    if ema7 is None or ema20 is None:
        return None
    if ema7 > ema20:
        return "uptrend"
    elif ema7 < ema20:
        return "downtrend"
    return None


class Ema:
    def __init__(self, period: int, prev: float | None = None):
        self.prev = prev
        self.buffer = []
        self.period = period
        self.k = 2 / (period + 1)

    def calculate(self, curr: float) -> float | None:
        if self.prev is None:
            self.buffer.append(curr)
            if len(self.buffer) == self.period:
                ema = sum(self.buffer) / len(self.buffer)
                self.buffer.clear()
            else:
                ema = None
        else:
            ema = (curr - self.prev) * self.k + self.prev

        self.prev = ema
        return ema
