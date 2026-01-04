from pyspark.errors.exceptions.base import AnalysisException
from pyspark.sql import SparkSession


def table_exists(spark: SparkSession, database: str, table: str) -> bool:
    try:
        spark.catalog.getTable(f"{database}.{table}")
        return True
    except AnalysisException:
        return False

def database_exists(spark: SparkSession, database) -> bool:
    try:
        spark.catalog.getDatabase(database)
        return True
    except AnalysisException:
        return False