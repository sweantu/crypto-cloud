export AWS_PROFILE="default"
export AWS_SSO_CACHE="$HOME/.aws/cli/cache"
mkdir -p "$AWS_SSO_CACHE"

# -----------------------------
# Load cached AWS credentials
# -----------------------------
load_cached_creds() {
  CREDS_FILE="$AWS_SSO_CACHE/${AWS_PROFILE}_sts.json"
  if [[ -f "$CREDS_FILE" ]]; then
    export AWS_ACCESS_KEY_ID=$(jq -r '.accessKeyId // empty' "$CREDS_FILE")
    export AWS_SECRET_ACCESS_KEY=$(jq -r '.secretAccessKey // empty' "$CREDS_FILE")
    export AWS_SESSION_TOKEN=$(jq -r '.sessionToken // empty' "$CREDS_FILE")
  fi
}

# -----------------------------
# Save credentials to cache
# -----------------------------
cache_creds() {
  CREDS_FILE="$AWS_SSO_CACHE/${AWS_PROFILE}_sts.json"
  # read from stdin and write directly to file
  cat > "$CREDS_FILE"
}

# -----------------------------
# Refresh SSO + role creds
# -----------------------------
refresh_sso_creds() {
  echo "🔄 AWS SSO expired → running login..."
  aws sso login --profile "$AWS_PROFILE"

  CACHE_DIR="$HOME/.aws/sso/cache"
  CACHE_FILE=$(ls -t "$CACHE_DIR"/*.json 2>/dev/null | head -n 1)

  ACCESS_TOKEN=$(jq -r '.accessToken // empty' "$CACHE_FILE")
  ACCOUNT_ID=$(aws configure get sso_account_id --profile "$AWS_PROFILE")
  ROLE_NAME=$(aws configure get sso_role_name --profile "$AWS_PROFILE")

  SSO_CREDS_JSON=$(aws sso get-role-credentials \
      --profile "$AWS_PROFILE" \
      --access-token "$ACCESS_TOKEN" \
      --account-id "$ACCOUNT_ID" \
      --role-name "$ROLE_NAME")

  # export env vars from response
  export AWS_ACCESS_KEY_ID=$(echo "$SSO_CREDS_JSON" | jq -r '.roleCredentials.accessKeyId // empty')
  export AWS_SECRET_ACCESS_KEY=$(echo "$SSO_CREDS_JSON" | jq -r '.roleCredentials.secretAccessKey // empty')
  export AWS_SESSION_TOKEN=$(echo "$SSO_CREDS_JSON" | jq -r '.roleCredentials.sessionToken // empty')

  # write only roleCredentials into our cache
  echo "$SSO_CREDS_JSON" | jq '.roleCredentials' | cache_creds

  echo "✅ Loaded new AWS SSO role credentials"
}

# -----------------------------
# Check creds on each terminal
# -----------------------------
check_aws_creds() {
  # Try load cached creds first
  load_cached_creds

  aws sts get-caller-identity >/dev/null 2>&1
  if [[ $? -ne 0 ]]; then
    refresh_sso_creds
  fi
}

check_aws_creds