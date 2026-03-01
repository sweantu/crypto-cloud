import logging

from shared_lib.arg import get_args, get_glue_args
from shared_lib.local import LOCAL_ENV, LOCAL_RUN
from shared_lib.spark import get_spark_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



if __name__ == "__main__":
    from transformation.klines.main import run

    args_list = [
        "symbol",
        "landing_date",
        "data_lake_bucket",
        "transform_db",
        "iceberg_lock_table",
    ]
    args = get_args(args_list) if LOCAL_ENV else get_glue_args(args_list)
    symbol = args["symbol"]
    landing_date = args["landing_date"]

    data_lake_bucket = args["data_lake_bucket"]
    iceberg_lock_table = args["iceberg_lock_table"]
    transform_db = args["transform_db"]

    spark = get_spark_session(
        app_name="klines_transform_job",
        local_run=LOCAL_RUN,
        minio=LOCAL_ENV,
        hive=LOCAL_ENV,
        glue=not LOCAL_ENV,
        iceberg_lock_table=iceberg_lock_table,
    )
    run(
        spark,
        symbol,
        landing_date,
        data_lake_bucket=data_lake_bucket,
        transform_db=transform_db,
    )
