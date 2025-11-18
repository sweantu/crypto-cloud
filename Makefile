TF_STATE=terraform/terraform.tfstate
ins?=clickhouse

INSTANCE_ID_CMD=terraform output -state=$(TF_STATE) -raw $(ins)_instance_id
INSTANCE_IP_CMD=aws ec2 describe-instances --instance-ids $$($(INSTANCE_ID_CMD)) --query "Reservations[0].Instances[0].PublicIpAddress" --output text


ssh:
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$($(INSTANCE_IP_CMD))

log-ec2:
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$($(INSTANCE_IP_CMD)) "sudo cat /var/log/cloud-init-output.log | tail -200"

log-ec2-docker:
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$($(INSTANCE_IP_CMD)) "sudo docker logs $(ins) | tail -200"

stop-ec2:
	aws ec2 stop-instances --instance-ids $$($(INSTANCE_ID_CMD))

start-ec2:
	aws ec2 start-instances --instance-ids $$($(INSTANCE_ID_CMD))

describe-ec2:
	aws ec2 describe-instances \
		--instance-ids $$($(INSTANCE_ID_CMD)) \
		--query "Reservations[].Instances[]" \
		--output table
sync-clickhouse:
	rsync -avz -e "ssh -i ~/.ssh/$(KEY_NAME)" clickhouse/ ubuntu@$$($(INSTANCE_IP_CMD)):/home/ubuntu/clickhouse/