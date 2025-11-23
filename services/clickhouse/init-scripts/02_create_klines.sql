-- Klines table
CREATE TABLE IF NOT EXISTS klines (
    window_start DateTime64(3, 'UTC'),
    window_end DateTime64(3, 'UTC'),
    symbol String,
    landing_date Date,
    open_price Float64,
    high_price Float64,
    low_price Float64,
    close_price Float64,
    volume Float64,
    created_at Date DEFAULT toDate(now('UTC'))
) ENGINE = MergeTree()
PARTITION BY (symbol, landing_date)
ORDER BY (symbol, window_start);