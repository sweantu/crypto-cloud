CREATE TABLE IF NOT EXISTS indicators (
    window_start DateTime64(3, 'UTC'),
    window_end DateTime64(3, 'UTC'),
    symbol String,
    landing_date Date,
    open_price Float64,
    high_price Float64,
    low_price Float64,
    close_price Float64,
    volume Float64,
    rsi6 Nullable(Float64),
    rsi_ag Nullable(Float64),
    rsi_al Nullable(Float64),
    ema7 Nullable(Float64),
    ema20 Nullable(Float64),
    ema12 Nullable(Float64),
    ema26 Nullable(Float64),
    macd Nullable(Float64),
    signal Nullable(Float64),
    histogram Nullable(Float64),
    trend Nullable(String),
    pattern Nullable(String),
    created_at Date DEFAULT toDate(now('UTC'))
) ENGINE = MergeTree()
PARTITION BY (symbol, landing_date)
ORDER BY (symbol, window_start);