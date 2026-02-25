class Rsi:
    def __init__(
        self,
        period: int,
        prev: float | None = None,
        prev_ag: float | None = None,
        prev_al: float | None = None,
    ):
        self.prev = prev
        self.prev_ag = prev_ag
        self.prev_al = prev_al
        self.buffer = []
        self.period = period

    def calculate(self, curr: float) -> float | None:
        if self.prev is None:
            diff = None
        else:
            diff = curr - self.prev
        self.prev = curr

        rsi = None
        if diff is None:
            return rsi

        if self.prev_ag is None or self.prev_al is None:
            self.buffer.append(diff)

            if len(self.buffer) < self.period:
                return rsi

            ag = sum(d for d in self.buffer if d > 0) / self.period
            al = sum(-d for d in self.buffer if d < 0) / self.period
            self.buffer.clear()
        else:
            ag = (
                (self.prev_ag * (self.period - 1)) + (diff if diff > 0 else 0.0)
            ) / self.period
            al = (
                (self.prev_al * (self.period - 1)) + (-diff if diff < 0 else 0.0)
            ) / self.period
        self.prev_ag = ag
        self.prev_al = al

        if al == 0:
            rsi = 100.0
        elif ag == 0:
            rsi = 0.0
        else:
            rs = ag / al
            rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi