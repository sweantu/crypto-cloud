CREATE TABLE IF NOT EXISTS output (
    ticker String,
    price Float64,
    event_time DateTime64(3, 'UTC')
) ENGINE = MergeTree()
PARTITION BY (ticker)
ORDER BY (event_time);