# macd.py
import logging

from common.ema import calc_ema
from shared_lib.number import round_half_up

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_macd_in_chunks(
    prev_ema12=None,
    prev_ema26=None,
    prev_signal=None,
):
    def macd_in_chunks(iterator):
        ema_configs = {
            "ema12": {
                "period": 12,
                "k": 2 / (12 + 1),
                "prev": prev_ema12,
                "buffer": [],
            },
            "ema26": {
                "period": 26,
                "k": 2 / (26 + 1),
                "prev": prev_ema26,
                "buffer": [],
            },
            "signal": {
                "period": 9,
                "k": 2 / (9 + 1),
                "prev": prev_signal,
                "buffer": [],
            },
        }

        for pdf in iterator:
            ema12_vals = []
            ema26_vals = []
            macd_vals = []
            signal_vals = []
            hist_vals = []

            for p in pdf["close_price"]:
                price = float(p)

                # 1️⃣ EMA fast / slow
                e12 = calc_ema(price, ema_configs["ema12"])
                e26 = calc_ema(price, ema_configs["ema26"])

                ema12_vals.append(round_half_up(e12, 2) if e12 is not None else None)
                ema26_vals.append(round_half_up(e26, 2) if e26 is not None else None)

                # 2️⃣ MACD line
                macd = e12 - e26 if e12 is not None and e26 is not None else None
                macd_vals.append(round_half_up(macd, 2) if macd is not None else None)

                # 3️⃣ Signal line (EMA of MACD)
                signal = calc_ema(macd, ema_configs["signal"])
                signal_vals.append(
                    round_half_up(signal, 2) if signal is not None else None
                )

                # 4️⃣ Histogram
                hist = (
                    macd - signal if macd is not None and signal is not None else None
                )
                hist_vals.append(round_half_up(hist, 2) if hist is not None else None)

            pdf["ema12"] = ema12_vals
            pdf["ema26"] = ema26_vals
            pdf["macd"] = macd_vals
            pdf["signal"] = signal_vals
            pdf["histogram"] = hist_vals

            pdf = pdf[
                [*pdf.columns[:-5], "ema12", "ema26", "macd", "signal", "histogram"]
            ]
            yield pdf

    logger.info(
        f"Using previous MACD state: ema12={prev_ema12}, ema26={prev_ema26}, signal={prev_signal}"
    )
    return macd_in_chunks
