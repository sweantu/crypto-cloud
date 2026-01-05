#!/usr/bin/env bash

export PYTHONPATH="$ROOT_DIR/apps/crypto_data/"

pyenv shell spark

if ! python -c "import shared_lib" >/dev/null 2>&1; then
  pip install -e "$ROOT_DIR/apps/shared_lib"
fi

if [ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]; then
  source "$HOME/.sdkman/bin/sdkman-init.sh"
fi
sdk use java 17.0.17-tem

echo "✅ Spark environment setup completed successfully"