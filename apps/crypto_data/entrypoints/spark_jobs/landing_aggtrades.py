from ingestion.landing_aggtrades.main import run
from shared_lib.arg import get_args, get_glue_args
from shared_lib.local import LOCAL_ENV, LOCAL_RUN
from shared_lib.spark import (
    get_spark_session,
)


def main():
    args_list = ["date", "data_lake_bucket"]
    args = get_args(args_list) if LOCAL_ENV else get_glue_args(args_list)
    date = args["date"]
    data_lake_bucket = args["data_lake_bucket"]

    spark = get_spark_session(
        app_name="Aggtrades Ingestion Job", local_run=LOCAL_RUN, minio=LOCAL_ENV
    )

    run(
        spark,
        date,
        data_lake_bucket=data_lake_bucket,
    )


if __name__ == "__main__":
    main()
