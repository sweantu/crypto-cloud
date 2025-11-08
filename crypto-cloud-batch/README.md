### Python 3.11

#### Spark test

```bash
python test.py
spark-submit test.py
```

#### Data lake
```bash
aws sts get-caller-identity
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
#### ECS
```bash
# find ecs task arn
aws ecs list-tasks --cluster crypto-cloud-dev-650251698703-grafana-cluster --service-name grafana-service
aws ecs describe-tasks --cluster crypto-cloud-dev-650251698703-grafana-cluster --tasks arn:aws:ecs:ap-southeast-1:650251698703:task/crypto-cloud-dev-650251698703-grafana-cluster/4ab16eca1c8b4110a6bcd3d4d9b69cd1

# find instance public ip
eni=$(aws ecs describe-tasks \
  --cluster crypto-cloud-dev-650251698703-grafana-cluster \
  --tasks arn:aws:ecs:ap-southeast-1:650251698703:task/crypto-cloud-dev-650251698703-grafana-cluster/4ab16eca1c8b4110a6bcd3d4d9b69cd1 \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text)
aws ec2 describe-network-interfaces \
  --network-interface-ids $eni \
  --query "NetworkInterfaces[0].Association.PublicIp" \
  --output text

# access ecs container
aws ecs execute-command \
  --cluster crypto-cloud-dev-650251698703-grafana-cluster \
  --task arn:aws:ecs:ap-southeast-1:650251698703:task/crypto-cloud-dev-650251698703-grafana-cluster/4ab16eca1c8b4110a6bcd3d4d9b69cd1 \
  --interactive \
  --command "bash"

# read log container
aws logs tail /ecs/grafana --follow
```