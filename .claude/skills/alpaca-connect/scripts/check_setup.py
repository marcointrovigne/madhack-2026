"""Verify Alpaca Connect (OAuth) app credentials are present.

This does NOT make a live API call (that would require a real user token).
It only validates that the client credentials are configured and the authorize
URL builds correctly.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlencode


def main() -> int:
    client_id = os.environ.get("ALPACA_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("ALPACA_OAUTH_CLIENT_SECRET")
    redirect_uri = os.environ.get("ALPACA_OAUTH_REDIRECT_URI")
    missing = [n for n, v in [
        ("ALPACA_OAUTH_CLIENT_ID", client_id),
        ("ALPACA_OAUTH_CLIENT_SECRET", client_secret),
        ("ALPACA_OAUTH_REDIRECT_URI", redirect_uri),
    ] if not v]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}")
        return 1

    url = "https://app.alpaca.markets/oauth/authorize?" + urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "account:write trading",
        "state": "dummy",
    })
    print(f"OK  authorize url builds: {url[:80]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
