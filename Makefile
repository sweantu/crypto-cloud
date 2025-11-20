TF_STATE=terraform/terraform.tfstate
TERRAFORM_OUTPUT=terraform output -state=$(TF_STATE) -raw
REGION=ap-southeast-1

ssh:
	@ins="$(ins)"; \
	[ -z "$$ins" ] && ins="clickhouse"; \
	echo "ins=$$ins" ; \
	instance_id="$$( $(TERRAFORM_OUTPUT) $${ins}_instance_id )"; \
	instance_ip="$$( aws ec2 describe-instances --instance-ids "$$instance_id" --query "Reservations[0].Instances[0].PublicIpAddress" --output text )"; \
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$instance_ip

log-ec2:
	@ins="$(ins)"; \
	[ -z "$$ins" ] && ins="clickhouse"; \
	echo "ins=$$ins" ; \
	instance_id="$$( $(TERRAFORM_OUTPUT) $${ins}_instance_id )"; \
	instance_ip="$$( aws ec2 describe-instances --instance-ids "$$instance_id" --query "Reservations[0].Instances[0].PublicIpAddress" --output text )"; \
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$instance_ip "sudo cat /var/log/cloud-init-output.log | tail -200"

log-ec2-docker:
	@ins="$(ins)"; \
	[ -z "$$ins" ] && ins="clickhouse"; \
	echo "ins=$$ins" ; \
	instance_id="$$( $(TERRAFORM_OUTPUT) $${ins}_instance_id )"; \
	instance_ip="$$( aws ec2 describe-instances --instance-ids "$$instance_id" --query "Reservations[0].Instances[0].PublicIpAddress" --output text )"; \
	ssh -i ~/.ssh/$(KEY_NAME) ubuntu@$$instance_ip "sudo docker logs $$ins | tail -200"

stop-ec2:
	@ins="$(ins)"; \
	[ -z "$$ins" ] && ins="clickhouse"; \
	echo "ins=$$ins" ; \
	instance_id="$$( $(TERRAFORM_OUTPUT) $${ins}_instance_id )"; \
	aws ec2 stop-instances --instance-ids $$instance_id

start-ec2:
	@ins="$(ins)"; \
	[ -z "$$ins" ] && ins="clickhouse"; \
	echo "ins=$$ins" ; \
	instance_id="$$( $(TERRAFORM_OUTPUT) $${ins}_instance_id )"; \
	aws ec2 start-instances --instance-ids $$instance_id

describe-ec2:
	@ins="$(ins)"; \
	[ -z "$$ins" ] && ins="clickhouse"; \
	echo "ins=$$ins" ; \
	instance_id="$$( $(TERRAFORM_OUTPUT) $${ins}_instance_id )"; \
	aws ec2 describe-instances \
		--instance-ids "$$instance_id" \
		--query "Reservations[].Instances[]" \
		--output table

sync-clickhouse:
	@instance_id="$$( $(TERRAFORM_OUTPUT) clickhouse_instance_id )"; \
	instance_ip="$$( aws ec2 describe-instances --instance-ids "$$instance_id" --query "Reservations[0].Instances[0].PublicIpAddress" --output text )"; \
	rsync -avz -e "ssh -i ~/.ssh/$(KEY_NAME)" clickhouse/ ubuntu@$$instance_ip:/home/ubuntu/clickhouse/

jupyter-convert:
	@path="$(path)"; \
	[ -z "$$path" ] && path="example.ipynb"; \
	echo "path=$$path" ; \
	jupyter nbconvert --to script $$path

spark-submit:
	@script="$(script)"; \
	[ -z "$$script" ] && script="spark_job.py"; \
	echo "script=$$script" ; \
	spark-submit \
		--master "local[*]" \
		--conf "spark.driver.memory=2g" \
		--conf "spark.executor.memory=1g" \
		--conf "spark.sql.shuffle.partitions=2" \
		$$script

sync-glue-scripts:
	@glue_scripts_bucket_name="$$($(TERRAFORM_OUTPUT) glue_scripts_bucket_name)"; \
	aws s3 sync ./services/spark-jobs s3://$$glue_scripts_bucket_name --exclude "*" --include "*.py" --delete

start-glue-job:
	@job="$(job)"; \
	[ -z "$$job" ] && job="landing_job"; \
	echo "job=$$job" ; \
	symbol="$(symbol)"; \
	[ -z "$$symbol" ] && symbol="ADAUSDT"; \
	echo "symbol=$$symbol" ; \
	landing_date="$(landing_date)"; \
	[ -z "$$landing_date" ] && landing_date="2025-09-27"; \
	echo "landing_date=$$landing_date" ; \
	job_name="$$($(TERRAFORM_OUTPUT) "$${job}_name")"; \
	aws glue start-job-run \
		--job-name $$job_name \
		--arguments "{ \
			\"--symbol\":\"$$symbol\", \
			\"--landing_date\":\"$$landing_date\" \
		}"

get-glue-job-status:
	@job_run_id="$(job_run_id)"; \
	[ -z "$$job_run_id" ] && { echo "job_run_id is required" ; exit 1 ; } ; \
	job="$(job)"; \
	[ -z "$$job" ] && job="landing_job"; \
	echo "job=$$job" ; \
	job_name="$$($(TERRAFORM_OUTPUT) "$${job}_name")"; \
	aws glue get-job-run \
		--job-name $$job_name \
		--run-id "$$job_run_id"

push-airflow-image:
	@airflow_repo_url="$$($(TERRAFORM_OUTPUT) airflow_repo_url)"; \
	account_id="$$($(TERRAFORM_OUTPUT) account_id)"; \
	aws ecr get-login-password --region $(REGION) | \
	    docker login --username AWS --password-stdin $${account_id}.dkr.ecr.$(REGION).amazonaws.com ; \
	docker buildx build \
	  --platform linux/amd64 \
	  -f airflow/Dockerfile \
	  -t $$airflow_repo_url:latest \
	  --push .

log-ecs:
	@task="$(task)"; \
	[ -z "$$task" ] && task="airflow"; \
	echo "task=$$task" ; \
	aws logs tail /ecs/$$task | tail -200

describe-rds:
	@iden="$(iden)"; \
	[ -z "$$iden" ] && iden="airflow_db"; \
	echo "iden=$$iden" ; \
	db_instance_identifier="$$($(TERRAFORM_OUTPUT) "$${iden}_identifier")"; \
	aws rds describe-db-instances \
		--db-instance-identifier "$$db_instance_identifier" \
		--query "DBInstances[]" \
		--output table

stop-rds:
	@iden="$(iden)"; \
	[ -z "$$iden" ] && iden="airflow_db"; \
	echo "iden=$$iden" ; \
	db_instance_identifier="$$($(TERRAFORM_OUTPUT) "$${iden}_identifier")"; \
	aws rds stop-db-instance --db-instance-identifier "$$db_instance_identifier"

start-rds:
	@iden="$(iden)"; \
	[ -z "$$iden" ] && iden="airflow_db"; \
	echo "iden=$$iden" ; \
	db_instance_identifier="$$($(TERRAFORM_OUTPUT) "$${iden}_identifier")"; \
	aws rds start-db-instance --db-instance-identifier "$$db_instance_identifier"