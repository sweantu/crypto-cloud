ACCOUNT_ID=650251698703
REGION=ap-southeast-1
REPO_NAME=crypto-cloud-batch-airflow-adm64

build:
	docker buildx build \
	  --platform linux/amd64 \
	  -f docker/airflow.Dockerfile \
	  -t ${REPO_NAME}:latest .
	
push:
	docker tag ${REPO_NAME}:latest \
		${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest
	aws ecr get-login-password --region ${REGION} | \
		docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
	aws ecr create-repository \
	  --repository-name ${REPO_NAME} \
	  --image-scanning-configuration scanOnPush=true \
	  --region ${REGION} || true
	docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:latest