from shared_lib.arg import get_args
from shared_lib.minio import upload_to_minio
from shared_lib.spark import get_spark_session

if __name__ == "__main__":
    from ingestion.aggtrades.main import ingest_aggtrades

    args = get_args(["symbol", "landing_date", "data_lake_bucket"])
    symbol = args["symbol"]
    landing_date = args["landing_date"]
    data_lake_bucket = args["data_lake_bucket"]

    spark = get_spark_session("Aggtrades Ingestion Job")
    ingest_aggtrades(
        spark,
        symbol,
        landing_date,
        data_lake_bucket=data_lake_bucket,
        upload_file=upload_to_minio,
    )
