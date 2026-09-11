"""Read-only Webull historical bars example, verified against SDK 3.0.0 source.
Network access occurs only with --fetch. Default endpoint is UAT.
Credentials belong in your local environment, never in a browser.
"""
import argparse
import json
from pathlib import Path


def fetch_bars(symbol="AAPL", environment="uat"):
    import os
    import logging
    from webull.core.client import ApiClient
    from webull.data.data_client import DataClient

    endpoints = {
        "uat": "th-api.uat.webullbroker.com",
        "production": "api.webull.co.th",
    }
    client = ApiClient(
        os.environ["WEBULL_APP_KEY"],
        os.environ["WEBULL_APP_SECRET"],
        "th",
    )
    client.add_endpoint("th", endpoints[environment])
    client.set_stream_logger(log_level=logging.CRITICAL)
    data_client = DataClient(client)
    response = data_client.market_data.get_batch_history_bar(
        symbols=[symbol],
        category="US_STOCK",
        timespan="D",
        count=120,
        real_time_required=True,
        trading_sessions="RTH",
    )
    if response.status_code != 200:
        raise RuntimeError("Webull HTTP " + str(response.status_code))
    return response.json()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Explicitly request market data")
    parser.add_argument("--environment", choices=["uat", "production"], default="uat")
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--output", type=Path, default=Path("webull_bars.json"))
    args = parser.parse_args()
    if not args.fetch:
        print("No network request. Set WEBULL_APP_KEY and WEBULL_APP_SECRET locally.")
        print("Then run: python webull_bars.py --fetch --environment uat")
        return
    if args.output.exists():
        raise SystemExit("Output exists. Choose a new --output file.")
    try:
        payload = fetch_bars(args.symbol, args.environment)
        if not isinstance(payload, dict) or not isinstance(payload.get("result"), list):
            raise ValueError("Unexpected response schema; check current API documentation")
        with args.output.open("x", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        print("Saved market data to", args.output)
        print("Validate timestamps, completed sessions and adjustment conventions before use.")
    except KeyError:
        raise SystemExit("Set the required environment variables on this machine.")
    except Exception as exc:
        raise SystemExit("Request did not complete: " + type(exc).__name__ +
                         ". Check environment, 2FA and OpenAPI market-data permissions.") from None


if __name__ == "__main__":
    main()
