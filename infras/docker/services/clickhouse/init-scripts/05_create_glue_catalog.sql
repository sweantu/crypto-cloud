SET allow_experimental_database_glue_catalog = 1;
CREATE DATABASE IF NOT EXISTS glue_catalog
engine = DataLakeCatalog
settings
    catalog_type = 'glue',
    region = 'ap-southeast-1',
    aws_access_key_id = '${CLICKHOUSE_AWS_ACCESS_KEY_ID}',
    aws_secret_access_key = '${CLICKHOUSE_AWS_SECRET_ACCESS_KEY}';