#!/bin/bash
set -e
# --- Assign variables ---
project_prefix=${1:-crypto-cloud-dev-583323753643}
echo "✅Project prefix: $project_prefix"

db_list=$(aws glue get-databases --query "DatabaseList[].Name" --output text | tr '\t' '\n' | grep "${project_prefix//-/_}" || true)
if [ -z "$db_list" ]; then
  echo "⚠️  No Glue databases found for prefix: ${project_prefix//-/_}"
else
  echo "🧹 Found databases:"
  echo "$db_list"
  # --- Delete each Glue database ---
  for db_name in $db_list; do
    echo
    echo "🧹 Deleting Glue database: $db_name ..."
    aws glue delete-database --name "$db_name" --no-cli-pager || echo "⚠️  Failed to delete $db_name"
    echo "✅ Deleted Glue database $db_name"
  done
fi

# --- Empty S3 Bucket ---
echo
bucket_name="$project_prefix-data-lake-bucket"
echo "🧹 Emptying S3 bucket: s3://$bucket_name ..."
aws s3 rm "s3://$bucket_name" --recursive --no-cli-pager || echo "⚠️  Bucket $bucket_name not found or already empty."
echo "✅ Emptied S3 bucket '$bucket_name'"

echo
echo "🎯 Cleanup complete for project_prefix: $project_prefix"