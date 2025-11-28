#!/usr/bin/env bash
set -euo pipefail

rm -rf package lambda.zip
mkdir package

pip install -r requirements.txt -t package

cp main.py package

cd package
zip -r ../lambda.zip .
cd ..
echo "lambda.zip built successfully"