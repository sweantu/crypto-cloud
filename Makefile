docker-network-create:
	docker network create crypto-cloud-network

docker-batch-storage-up:
	docker-compose -p crypto-cloud-batch-storage -f infras/docker/docker-compose.batch-storage.yml up -d --remove-orphans

docker-batch-storage-down:
	docker-compose -p crypto-cloud-batch-storage -f infras/docker/docker-compose.batch-storage.yml down

docker-batch-processing-up:
	docker-compose -p crypto-cloud-batch-processing -f infras/docker/docker-compose.batch-processing.yml up -d --remove-orphans

docker-batch-processing-down:
	docker-compose -p crypto-cloud-batch-processing -f infras/docker/docker-compose.batch-processing.yml down

docker-stream-storage-up:
	docker-compose -p crypto-cloud-stream-storage -f infras/docker/docker-compose.stream-storage.yml up -d --remove-orphans

docker-stream-storage-down:
	docker-compose -p crypto-cloud-stream-storage -f infras/docker/docker-compose.stream-storage.yml down

docker-minio-create-bucket:
	docker exec -i crypto-cloud-minio sh -c '\
		mc alias set local http://localhost:9000 $(MINIO_USER) $(MINIO_PASSWORD) && \
		mc ls local/$(DATA_LAKE_BUCKET) >/dev/null 2>&1 || \
		mc mb local/$(DATA_LAKE_BUCKET)'

docker-clickhouse-client:
	docker exec -it crypto-cloud-clickhouse clickhouse-client -u $(CLICKHOUSE_USER) --password $(CLICKHOUSE_PASSWORD) --database $(CLICKHOUSE_DB)

docker-clickhouse-init:
	bash infras/docker/services/clickhouse/init.sh

SPARK_MASTER?=local[*]
SPARK_PACKAGES?=org.apache.hadoop:hadoop-aws:3.3.4,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,org.apache.iceberg:iceberg-aws-bundle:1.7.1
SPARK_JOBS_DIR?=apps/crypto_data/entrypoints/spark_jobs
spark-submit:
	$(eval LIBS := $(if $(with_libs),--py-files build/spark_jobs/$(job)_libs.zip,))
	$(eval ARGS :=)
	$(eval ARGS += --symbol $(symbol))
	$(eval ARGS += --landing_date $(landing_date))
	$(eval ARGS += --data_lake_bucket $(data_lake_bucket))
	$(eval ARGS += $(if $(transform_db),--transform_db $(transform_db),))
	$(eval ARGS += $(if $(iceberg_lock_table),--iceberg_lock_table $(iceberg_lock_table),))


	spark-submit \
		--master $(SPARK_MASTER) \
		--packages $(SPARK_PACKAGES) \
		$(LIBS) \
		"$(SPARK_JOBS_DIR)/$(job).py" \
		$(ARGS)

RSYNC_EXCLUDES?=--exclude='__pycache__/' --exclude='*.pyc'
rsync-local:
	rsync -avz $(RSYNC_EXCLUDES) $(src) $(dst)

zip:
	cd build/tmp && zip -r ../$(dst) .

build-artifacts:
	rm -rf build/tmp build/$(dir)/$(job)_libs.zip && mkdir -p build/tmp build/$(dir)
	make rsync-local src=apps/shared_lib/src/shared_lib dst=build/tmp
	make rsync-local src=apps/crypto_data/common dst=build/tmp
	make rsync-local src=apps/crypto_data/$(stage)/$(job) dst=build/tmp/$(stage)
	make zip dst=$(dir)/$(job)_libs.zip

airflow-start:
	bash apps/crypto_data/orchestration/airflow/entrypoint.sh

terraform-init:
	cd infras/terraform && terraform init
terraform-plan:
	cd infras/terraform && terraform plan
terraform-apply:
	cd infras/terraform && terraform apply -auto-approve
terraform-destroy:
	cd infras/terraform && terraform destroy
terraform-output:
	cd infras/terraform && terraform output
terraform-var:
	terraform output -state=$(TF_STATE) -raw $(var)

ec2-ip:
	instance_id="$$( $(MAKE) -s terraform-var var=$(ins)_instance_id )"; \
	aws ec2 describe-instances --instance-ids "$$instance_id" \
	  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

ec2-ssh:
	instance_ip="$$($(MAKE) -s ec2-ip ins=$(ins))"; \
	ssh -i ~/.ssh/$$SSH_KEY ubuntu$$instance_ip

ec2-log:
	instance_ip="$$($(MAKE) -s ec2-ip ins=$(ins))"; \
	ssh -i ~/.ssh/$$SSH_KEY ubuntu$$instance_ip "sudo cat /var/log/cloud-init-output.log | tail -200"

ec2-stop:
	instance_id="$$( $(MAKE) -s terraform-var var=$(ins)_instance_id )"; \
	aws ec2 stop-instances --instance-ids $$instance_id

ec2-start:
	instance_id="$$( $(MAKE) -s terraform-var var=$(ins)_instance_id )"; \
	aws ec2 start-instances --instance-ids $$instance_id

ec2-describe:
	instance_id="$$( $(MAKE) -s terraform-var var=$(ins)_instance_id )"; \
	aws ec2 describe-instances --instance-ids $$instance_id --query "Reservations[0].Instances[]" --output table

ec2-run:
	instance_ip="$$($(MAKE) -s ec2-ip ins=$(ins))"; \
	ssh -t -i "$$HOME/.ssh/$(SSH_KEY)" ubuntu$$instance_ip '$(cmd)'

ec2-clickhouse:
	$(MAKE) -s ec2-run ins=clickhouse \
		cmd='\
		cd clickhouse && \
		set -a && . ./env.sh && set +a && \
		docker exec -it crypto-cloud-clickhouse clickhouse-client -u $$$$CLICKHOUSE_USER --password $$$$CLICKHOUSE_PASSWORD --database $$$$CLICKHOUSE_DB \
		'
ec2-clickhouse2:
	$(MAKE) -s ec2-run ins=clickhouse \
		cmd='\
		docker exec -it crypto-cloud-clickhouse clickhouse-client -u $(CLICKHOUSE_USER) --password $(CLICKHOUSE_PASSWORD) --database $(CLICKHOUSE_DB) \
		'
ec2-rsync:
	instance_ip="$$($(MAKE) -s ec2-ip ins=$(ins))"; \
	rsync -avz -e "ssh -i ~/.ssh/$$SSH_KEY" $(src) ubuntu$$instance_ip:/home/ubuntu/$(dst)

glue-scripts-sync:
	aws s3 sync build/spark_jobs s3://$(GLUE_SCRIPTS_DIRECTORY)
	aws s3 sync apps/crypto_data/entrypoints/spark_jobs s3://$(GLUE_SCRIPTS_DIRECTORY)


push-image:
	aws ecr get-login-password --region $(AWS_REGION) | \
	    docker login --username AWS --password-stdin $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com ; \
	docker buildx build \
	  --platform linux/amd64 \
	  -f apps/crypto_data/orchestration/airflow/Dockerfile \
	  -t $(REPO_URL):latest \
	  --push .

ecs-logs:
	aws logs tail /ecs/$(TASK) | tail -200

rds-describe:
	aws rds describe-db-instances \
		--db-instance-identifier $(db_instance_identifier) \
		--query "DBInstances[]" \
		--output table

rds-stop:
	aws rds stop-db-instance --db-instance-identifier $(db_instance_identifier)

start-rds:
	aws rds start-db-instance --db-instance-identifier $(db_instance_identifier)

invoke-lambda:
	aws lambda invoke \
		--cli-binary-format raw-in-base64-out \
		--function-name $(function_name) \
		--invocation-type Event \
		--payload file://lambda_input.json \
		lambda_output.json;