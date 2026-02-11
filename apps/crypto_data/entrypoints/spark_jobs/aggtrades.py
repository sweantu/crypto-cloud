import argparse

from common.spark import get_spark_session

# import sys
# from awsglue.utils import getResolvedOptions
from shared_lib.minio import upload_to_minio

# args = getResolvedOptions(
#     sys.argv,
#     [
#         "symbol",
#         "landing_date",
#         "data_lake_bucket",
#         "iceberg_lock_table",
#     ],
# )

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", required=True)
parser.add_argument("--landing_date", required=True)
parser.add_argument("--data_lake_bucket", required=True)
args = parser.parse_args().__dict__


symbol = args["symbol"]
landing_date = args["landing_date"]

DATA_LAKE_BUCKET = args["data_lake_bucket"]

if __name__ == "__main__":
    from ingestion.aggtrades.main import ingest_aggtrades

    spark = get_spark_session("Aggtrades Ingestion Job")
    ingest_aggtrades(
        spark,
        symbol,
        landing_date,
        data_lake_bucket=DATA_LAKE_BUCKET,
        upload_file=upload_to_minio,
    )
