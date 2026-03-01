from shared_lib.arg import get_args, get_glue_args
from shared_lib.local import LOCAL_ENV, LOCAL_RUN
from shared_lib.minio import upload_to_minio
from shared_lib.s3 import upload_to_s3
from shared_lib.spark import (
    get_spark_session,
)

if __name__ == "__main__":
    from ingestion.aggtrades.main import run

    args_list = ["symbol", "landing_date", "data_lake_bucket"]
    args = get_args(args_list) if LOCAL_ENV else get_glue_args(args_list)
    symbol = args["symbol"]
    landing_date = args["landing_date"]
    data_lake_bucket = args["data_lake_bucket"]

    spark = get_spark_session(
        app_name="Aggtrades Ingestion Job", local_run=LOCAL_RUN, minio=LOCAL_ENV
    )

    run(
        spark,
        symbol,
        landing_date,
        data_lake_bucket=data_lake_bucket,
        upload_file=upload_to_minio if LOCAL_ENV else upload_to_s3,
    )
