import os

from yarl import URL


def lambda_handler(event, context):
    region = os.getenv("REGION")
    stream_name = os.getenv("AGGTRADES_STREAM_NAME")
    symbols = event.get("symbols", [])
    landing_dates = event.get("landing_dates", [])
    print(f"Producing crypto trades for {symbols} on dates {landing_dates}")

    url = URL("https://crypto-cloud.dev?token=123")
    return {
        "original": str(url),
        "path": url.path,
        "query": url.query_string,
        "symbols": symbols,
        "landing_dates": landing_dates,
        "region": region,
        "stream_name": stream_name,
    }
