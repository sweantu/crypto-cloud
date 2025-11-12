-- Engulfings table
CREATE TABLE IF NOT EXISTS engulfings (
    window_start DateTime64(3, 'UTC'),
    window_end DateTime64(3, 'UTC'),
    symbol String,
    landing_date Date,
    open_price Float64,
    high_price Float64,
    low_price Float64,
    close_price Float64,
    volume Float64,
    ema7 Nullable(Float64),
    ema20 Nullable(Float64),
    trend Nullable(String),
    engulfing_pattern Nullable(String),
    created_at Date DEFAULT toDate(now('UTC'))
) ENGINE = MergeTree()
PARTITION BY (symbol, landing_date)
ORDER BY (symbol, window_start);