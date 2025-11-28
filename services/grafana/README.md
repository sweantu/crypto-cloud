```sql
SELECT DISTINCT symbol FROM testdb.engulfings ORDER BY symbol

SELECT
    window_start AS time,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    ema7,
    ema20,
    CASE
        WHEN engulfing_pattern IS NOT NULL THEN close_price
        ELSE NULL
    END AS engulfing_close
FROM testdb.engulfings
WHERE
    symbol = '${symbol}'
    AND window_start BETWEEN
        parseDateTimeBestEffortOrNull('${__from:date}')
        AND parseDateTimeBestEffortOrNull('${__to:date}')
ORDER BY window_start ASC;
```
