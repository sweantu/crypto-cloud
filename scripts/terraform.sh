TF_STATE=infras/terraform/terraform.tfstate
export ATHENA_OUTPUT_LOCATION=$(terraform output -state=$TF_STATE -raw athena_output_location)
export DATA_LAKE_BUCKET=$(terraform output -state=$TF_STATE -raw data_lake_bucket_name)
export ICEBERG_LOCK_TABLE=$(terraform output -state=$TF_STATE -raw iceberg_lock_table_name)
export PROJECT_PREFIX=$(terraform output -state=$TF_STATE -raw project_prefix)
export PROJECT_PREFIX_UNDERSCORE=$(terraform output -state=$TF_STATE -raw project_prefix_underscore)

echo "✅ Environment variables are set."