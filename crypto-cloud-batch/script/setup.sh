#!/bin/bash
# setup.sh — export temporary AWS credentials for PySpark local use
# Usage: source setup.sh [profile_name]
# Default profile: default

sdk use java 17.0.17-tem

PROFILE=${1:-default}

# Find the latest cached SSO credential file
CACHE_FILE=$(ls -t ~/.aws/cli/cache/*.json 2>/dev/null | head -n 1)

if [[ -z "$CACHE_FILE" ]]; then
  echo "❌ No cached AWS credentials found. Try 'aws sso login --profile $PROFILE' first."
  return 1 2>/dev/null || exit 1
fi

echo "🔍 Using cached credentials file: $CACHE_FILE"

# Extract and export keys
export AWS_ACCESS_KEY_ID=$(jq -r '.Credentials.AccessKeyId' "$CACHE_FILE")
export AWS_SECRET_ACCESS_KEY=$(jq -r '.Credentials.SecretAccessKey' "$CACHE_FILE")
export AWS_SESSION_TOKEN=$(jq -r '.Credentials.SessionToken' "$CACHE_FILE")

if [[ -z "$AWS_ACCESS_KEY_ID" || "$AWS_ACCESS_KEY_ID" == "null" ]]; then
  echo "❌ Failed to extract AWS credentials from cache. Ensure you're logged in with SSO."
  return 1 2>/dev/null || exit 1
fi

echo "✅ AWS credentials exported successfully."
echo "   AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"

export JUPYTER_TOKEN=123456
echo "✅ Jupyter token set to $JUPYTER_TOKEN"