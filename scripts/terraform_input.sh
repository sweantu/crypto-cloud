export TF_VAR_aws_profile=${AWS_PROFILE}
export TF_VAR_aws_region=${AWS_REGION}

export TF_VAR_airflow_admin_username=${AIRFLOW_ADMIN_USERNAME}
export TF_VAR_airflow_admin_password=${AIRFLOW_ADMIN_PASSWORD}
export TF_VAR_airflow_admin_email=${AIRFLOW_ADMIN_EMAIL}
export TF_VAR_airflow_db_username=${AIRFLOW_DB_USERNAME}
export TF_VAR_airflow_db_password=${AIRFLOW_DB_PASSWORD}
export TF_VAR_airflow_db_name=${AIRFLOW_DB_NAME}
export TF_VAR_airflow_fernet_key=${AIRFLOW_FERNET_KEY}

export TF_VAR_clickhouse_db=${CLICKHOUSE_DB}
export TF_VAR_clickhouse_user=${CLICKHOUSE_USER}
export TF_VAR_clickhouse_password=${CLICKHOUSE_PASSWORD}

export TF_VAR_environment=${ENV}

export TF_VAR_grafana_admin_username=${GRAFANA_ADMIN_USERNAME}
export TF_VAR_grafana_admin_password=${GRAFANA_ADMIN_PASSWORD}

export TF_VAR_project=${PROJECT}

export TF_VAR_ssh_key=${SSH_KEY}

export TF_VAR_data_lake_bucket=${DATA_LAKE_BUCKET}
export TF_VAR_iceberg_lock_table=${ICEBERG_LOCK_TABLE}
export TF_VAR_transform_db=${TRANSFORM_DB}