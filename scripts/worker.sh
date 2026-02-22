#!/usr/bin/env bash

export PYTHONPATH="$ROOT_DIR/apps/crypto_data/"

pyenv shell worker

if ! python -c "import shared_lib" >/dev/null 2>&1; then
  pip install -e "$ROOT_DIR/apps/shared_lib"
fi

echo "✅ Worker environment setup completed successfully"