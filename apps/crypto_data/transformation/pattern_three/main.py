from .spark import process_pattern_three_data


def transform_pattern_three(spark, transform_db, symbol, landing_date):
    klines_table = "klines"
    pattern_three_table = "pattern_three"
    process_pattern_three_data(
        spark, transform_db, symbol, landing_date, klines_table, pattern_three_table
    )
