aws glue delete-database --name iceberg_local_test
echo "✅ Deleted Glue database 'iceberg_local_test'"

aws s3 rm s3://pyspark-local-test-bucket --recursive
echo "✅ Emptied S3 bucket 'pyspark-local-test-bucket'"