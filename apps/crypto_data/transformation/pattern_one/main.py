from .spark import process_pattern_one


def run(spark, transform_db, symbol, landing_date):
    klines_table = "klines"
    pattern_one_table = "pattern_one"
    process_pattern_one(
        spark, transform_db, symbol, landing_date, klines_table, pattern_one_table
    )
