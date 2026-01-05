python main.py \
 --symbols '["ADAUSDT","SUIUSDT"]' \
 --landing_dates '["2025-09-27","2025-09-28"]'

docker run --rm \
  -e AGGTRADES_STREAM_NAME="$AGGTRADES_STREAM_NAME" \
  -e REGION="$REGION" \
  aggtrades-producer \
  --symbols '["ADAUSDT","SUIUSDT"]' \
  --landing_dates '["2025-09-27","2025-09-28"]'