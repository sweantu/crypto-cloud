python main.py --name $AGGTRADES_STREAM_NAME

docker run --rm \
  -e REGION="$REGION" \
  aggtrades-consumer \
  --name $AGGTRADES_STREAM_NAME