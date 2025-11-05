#!/bin/bash
# setup.sh — export temporary AWS credentials for PySpark local use
# Usage: source setup.sh [profile_name]
# Default profile: default

sdk use java 17.0.17-tem

PROFILE=${1:-default}
# --- Find the latest cached SSO credential file ---
CACHE_DIR="$HOME/.aws/sso/cache"
CACHE_FILE=$(ls -t "$CACHE_DIR"/*.json 2>/dev/null | head -n 1)
if [[ -z "$CACHE_FILE" ]]; then
  echo "❌ No cached AWS credentials found."
  echo "   Try running: aws sso login --profile $PROFILE"
  return 1 2>/dev/null || exit 1
fi
echo "🔍 Using cached credentials file: $CACHE_FILE"
SSO_CREDS_JSON=$(aws sso get-role-credentials \
    --profile "$PROFILE" \
    --access-token "$(jq -r '.accessToken // empty' "$CACHE_FILE" 2>/dev/null)" \
    --account-id "$(aws configure get sso_account_id --profile "$PROFILE" 2>/dev/null)" \
    --role-name "$(aws configure get sso_role_name --profile "$PROFILE" 2>/dev/null)" 2>/dev/null)
AWS_ACCESS_KEY_ID=$(echo "$SSO_CREDS_JSON" | jq -r '.roleCredentials.accessKeyId // empty')
AWS_SECRET_ACCESS_KEY=$(echo "$SSO_CREDS_JSON" | jq -r '.roleCredentials.secretAccessKey // empty')
AWS_SESSION_TOKEN=$(echo "$SSO_CREDS_JSON" | jq -r '.roleCredentials.sessionToken // empty')
# --- Validate credentials ---
if [[ -z "$AWS_ACCESS_KEY_ID" || "$AWS_ACCESS_KEY_ID" == "null" ]]; then
  echo "❌ Failed to extract AWS credentials from SSO cache or CLI."
  echo "   Run: aws sso login --profile $PROFILE"
  return 1 2>/dev/null || exit 1
fi
# --- Export environment variables ---
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN
echo "✅ AWS credentials exported successfully."
echo "   AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"

# --- Jupyter token ---
export JUPYTER_TOKEN=123456
echo "✅ Jupyter token set to $JUPYTER_TOKEN"