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


def detect_trend(ema7, ema20):
    if ema7 is None or ema20 is None:
        return None
    if ema7 > ema20:
        return "uptrend"
    elif ema7 < ema20:
        return "downtrend"
    return None


def detect_pattern_one(current, trend):
    if not current or not trend:
        return None

    op = current["open_price"]
    cp = current["close_price"]
    hp = current["high_price"]
    lp = current["low_price"]

    body = abs(cp - op)
    if body == 0:
        return None

    lower_shadow = min(op, cp) - lp
    upper_shadow = hp - max(op, cp)

    if lower_shadow >= 2 * body and upper_shadow <= 0.25 * body:
        if trend == "uptrend":
            return "hanging man"
        if trend == "downtrend":
            return "hammer"

    return None


def detect_pattern_two(current, previous, trend):
    if not previous or not trend:
        return None
    op_prev, cp_prev = previous["open_price"], previous["close_price"]
    op, cp = current["open_price"], current["close_price"]

    if (
        cp_prev < op_prev
        and cp > op
        and op < cp_prev
        and cp > op_prev
        and trend == "downtrend"
    ):
        return "bullish engulfing"
    if (
        cp_prev > op_prev
        and cp < op
        and op > cp_prev
        and cp < op_prev
        and trend == "uptrend"
    ):
        return "bearish engulfing"
    return None


def detect_pattern_three(c1, c2, c3, trend):
    if not c1 or not c2 or not c3 or not trend:
        return None

    o1, c1p = c1["open_price"], c1["close_price"]
    o2, c2p = c2["open_price"], c2["close_price"]
    o3, c3p = c3["open_price"], c3["close_price"]
    h2, l2 = c2["high_price"], c2["low_price"]

    body1 = abs(o1 - c1p)
    body2 = abs(o2 - c2p)
    range2 = h2 - l2 if h2 and l2 else None

    # --- Morning Star ---
    if (
        c1p < o1
        and body2 <= 0.5 * body1
        and c2p < c1p
        and o2 < c1p
        and c3p > o3
        and c3p >= (o1 + c1p) / 2
        and trend == "downtrend"
    ):
        return "morning star"

    # --- Evening Star ---
    if (
        c1p > o1
        and body2 <= 0.5 * body1
        and o2 > c1p
        and c2p > c1p
        and c3p < o3
        and c3p <= (o1 + c1p) / 2
        and trend == "uptrend"
    ):
        return "evening star"

    # --- Morning Doji Star ---
    if (
        c1p < o1
        and range2 is not None
        and body2 <= 0.1 * range2
        and c2p < c1p
        and o2 < c1p
        and c3p > o3
        and c3p >= (o1 + c1p) / 2
        and trend == "downtrend"
    ):
        return "morning doji star"

    # --- Evening Doji Star ---
    if (
        c1p > o1
        and range2 is not None
        and body2 <= 0.1 * range2
        and o2 > c1p
        and c2p > c1p
        and c3p < o3
        and c3p <= (o1 + c1p) / 2
        and trend == "uptrend"
    ):
        return "evening doji star"

    return None
