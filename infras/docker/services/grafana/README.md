```sql
SELECT DISTINCT symbol FROM testdb.indicators ORDER BY symbol

SELECT
    window_start AS time,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    rsi6,
    macd,
    signal,
    histogram,
    ema7,
    ema20,
    CASE
        WHEN pattern IS NOT NULL THEN close_price
        ELSE NULL
    END AS indicator_close
FROM testdb.indicators
WHERE
    symbol = '${symbol}'
    AND window_start BETWEEN
        parseDateTimeBestEffortOrNull('${__from:date}')
        AND parseDateTimeBestEffortOrNull('${__to:date}')
ORDER BY window_start ASC;
```
