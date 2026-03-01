export TF_STATE=infras/terraform/terraform.tfstate

export ACCOUNT_ID=$(terraform output -state=$TF_STATE -raw account_id)
export AVAILABILITY_ZONES=$(terraform output -state=$TF_STATE -json availability_zones | jq -r '.[]')
export PROJECT_PREFIX=$(terraform output -state=$TF_STATE -raw project_prefix)
export PROJECT_PREFIX_UNDERSCORE=$(terraform output -state=$TF_STATE -raw project_prefix_underscore)

export VPC_ID=$(terraform output -state=$TF_STATE -raw vpc_id)
export PUBLIC_SUBNET_IDS=$(terraform output -state=$TF_STATE -json public_subnet_ids | jq -r '.[]')

export DATA_LAKE_BUCKET=$(terraform output -state=$TF_STATE -raw data_lake_bucket_name)
export ICEBERG_LOCK_TABLE=$(terraform output -state=$TF_STATE -raw iceberg_lock_table_name)
export TRANSFORM_DB=$(terraform output -state=$TF_STATE -raw transform_db_name)

export GLUE_SCRIPTS_DIRECTORY=$(terraform output -state=$TF_STATE -raw glue_scripts_directory)

# export AGGTRADES_STREAM=$(terraform output -state=$TF_STATE -json stream_info_map | jq -r ".\"$AGGTRADES_STREAM\".name")
# export INDICATORS_STREAM=$(terraform output -state=$TF_STATE -json stream_info_map | jq -r ".\"$INDICATORS_STREAM\".name")
# export ATHENA_OUTPUT_LOCATION=$(terraform output -state=$TF_STATE -raw athena_output_location)