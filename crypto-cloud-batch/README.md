### Python 3.11

#### Spark test

```bash
python test.py
spark-submit test.py
```

#### Data lake
```bash
aws s3api list-objects --bucket pyspark-local-test-bucket
aws s3 rm s3://pyspark-local-test-bucket --recursive

aws s3api list-object-versions \
    --bucket pyspark-local-test-bucket \
    --output=json \
    --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}'
aws s3api delete-objects \
    --bucket pyspark-local-test-bucket \
    --delete "$(aws s3api list-object-versions \
    --bucket pyspark-local-test-bucket \
    --output=json \
    --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

aws glue get-tables --database-name iceberg_local_test
aws glue get-tables --database-name iceberg_local_test --query 'TableList[].Name' --output text
for tbl in $(aws glue get-tables --database-name iceberg_local_test \
           --query 'TableList[].Name' --output text); do
  aws glue delete-table --database-name iceberg_local_test --name $tbl
done
aws glue delete-database --name iceberg_local_test
```