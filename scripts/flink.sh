#!/usr/bin/env bash

export PYTHONPATH="$ROOT_DIR/apps/crypto_data/"

pyenv shell flink

if ! python -c "import shared_lib" >/dev/null 2>&1; then
  pip install -e "$ROOT_DIR/apps/shared_lib"
fi

if [ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]; then
  source "$HOME/.sdkman/bin/sdkman-init.sh"
fi
sdk use java 11.0.28-tem

echo "✅ Flink environment setup completed successfully"