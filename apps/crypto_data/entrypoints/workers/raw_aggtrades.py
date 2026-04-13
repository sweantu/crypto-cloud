from ingestion.raw_aggtrades.main import run
from shared_lib.arg import get_args, get_glue_args
from shared_lib.local import LOCAL_ENV
from shared_lib.minio import upload_to_minio
from shared_lib.s3 import upload_to_s3


def main():
    args_list = ["date", "data_lake_bucket"]
    args = get_args(args_list) if LOCAL_ENV else get_glue_args(args_list)
    date = args["date"]
    data_lake_bucket = args["data_lake_bucket"]

    run(
        date,
        data_lake_bucket=data_lake_bucket,
        upload_file=upload_to_minio if LOCAL_ENV else upload_to_s3,
    )


if __name__ == "__main__":
    main()
