TF_STATE=terraform/terraform.tfstate

ssh-clickhouse:
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$(terraform output -state=$(TF_STATE) -raw clickhouse_public_ip)

log-clickhouse-ec2:
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$(terraform output -state=$(TF_STATE) -raw clickhouse_public_ip) "cat /var/log/cloud-init-output.log | tail -200"

log-clickhouse:
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$(terraform output -state=$(TF_STATE) -raw clickhouse_public_ip) "docker logs clickhouse | tail -200"