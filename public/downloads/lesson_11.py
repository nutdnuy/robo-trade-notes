"""Webull OpenAPI preparation: five offline examples, synthetic data only.
No credentials, network calls, external dependencies, or trading requests.
"""

# %% 1. Choose an environment explicitly
HOSTS = {
    "test": "th-api.uat.webullbroker.com",
    "production": "api.webull.co.th",
}

def choose_host(environment):
    if environment not in HOSTS:
        raise ValueError("Choose test or production explicitly")
    return HOSTS[environment]

assert choose_host("test") == "th-api.uat.webullbroker.com"
try:
    choose_host("prodution")  # A typo must never silently choose production.
except ValueError:
    print("Unknown environment rejected")
else:
    raise AssertionError("Unknown environment was accepted")
print("Selected host:", choose_host("test"))

# %% 2. Interpret token status (a teaching example, not an SDK implementation)
TOKEN_ACTIONS = {
    "PENDING": "Complete verification in the Webull app",
    "NORMAL": "Token is active; check endpoint permissions separately",
    "EXPIRED": "Verification window elapsed; check the SDK token flow",
    "INVALID": "Token is unusable; check the SDK token flow",
}
status = "PENDING"
assert status != "NORMAL"
print(status, "->", TOKEN_ACTIONS.get(status, "Consult the current API documentation"))

# %% 3. Convert numeric strings and calculate a spread
import json
from decimal import Decimal

# Synthetic prices in USD per share; these were not returned by Webull.
snapshot = json.loads('{"symbol": "DEMO", "bid": "99.98", "ask": "100.02"}')
bid, ask = Decimal(snapshot["bid"]), Decimal(snapshot["ask"])
assert bid > 0 and ask >= bid
spread = ask - bid
assert spread == Decimal("0.04")
print(f'{snapshot["symbol"]} spread: {spread:.2f} USD per share')

# %% 4. Interpret an explicitly specified timestamp unit
from datetime import datetime, timezone, timedelta

# Synthetic millisecond timestamp, chosen only for this exercise.
quote_time_ms = 1788485400000
epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
quote_time = epoch + timedelta(milliseconds=quote_time_ms)
example_now = quote_time + timedelta(seconds=30)
age_seconds = (example_now - quote_time).total_seconds()
assert age_seconds == 30.0
print("Quote time (UTC):", quote_time.isoformat())
print("Age relative to the example clock:", age_seconds, "seconds")
# In production, use the endpoint's documented unit and timezone, not a guess.

# %% 5. Keep evidence for each permission separate
# All values here are simulated observations, not a live readiness test.
checks = {
    "environment": "test",
    "token_status": "NORMAL",
    "account_http_status": 200,
    "expected_account_present": True,
    "market_data_request_succeeded": False,
}
account_read_verified = (
    checks["token_status"] == "NORMAL"
    and checks["account_http_status"] == 200
    and checks["expected_account_present"]
)
market_data_verified = checks["market_data_request_succeeded"]
assert account_read_verified and not market_data_verified
print("Account read verified:", account_read_verified)
print("Market data verified:", market_data_verified)
print("Next: verify market-data access separately. No trade was submitted.")
