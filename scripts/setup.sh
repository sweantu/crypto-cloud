#!/usr/bin/env bash

if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [[ -n "${ZSH_VERSION:-}" ]]; then
  SCRIPT_PATH="${(%):-%x}"
else
  echo "❌ Unsupported shell"
  return 1 2>/dev/null || exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
export ROOT_DIR="$(dirname "$SCRIPT_DIR")"


export ENV_FILE="$ROOT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ .env not found at $ENV_FILE"
  return 1 2>/dev/null || exit 1
fi
echo "🔄 Loading env from $ENV_FILE"
set -a
source "$ENV_FILE"
set +a

# echo "🔄 Loading AWS credentials"
# source ./scripts/aws.sh

# echo "🔄 Loading Terraform input"
# source ./scripts/terraform_input.sh

# echo "🔄 Loading Terraform output"
# source ./scripts/terraform_output.sh

echo "✅ Setup completed successfully"