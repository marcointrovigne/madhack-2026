# Connect API — SDK Reference

Alpaca Connect implements a standard **OAuth 2.0 authorization-code grant**. There is no
Alpaca-specific SDK for the OAuth handshake itself — use `httpx` or `requests` for the
HTTP calls. The SDK (`alpaca-py`) enters only when you instantiate
`TradingClient(oauth_token=...)` with a token you already hold.

---

## 1. Authorization URL

Redirect the user to:

```
https://app.alpaca.markets/oauth/authorize
```

### Query parameters

| Parameter       | Required | Description                                                                 |
|-----------------|----------|-----------------------------------------------------------------------------|
| `response_type` | Yes      | Must be `code`                                                              |
| `client_id`     | Yes      | Your OAuth app's client ID from the app registration page                   |
| `redirect_uri`  | Yes      | Must exactly match the URI registered in the Alpaca OAuth app settings      |
| `scope`         | Yes      | Space-separated list of requested scopes (see section 5)                    |
| `state`         | Recommended | Opaque random string for CSRF protection; verify it on callback         |

### Example

```python
import os, secrets
from urllib.parse import urlencode

params = {
    "response_type": "code",
    "client_id": os.environ["ALPACA_OAUTH_CLIENT_ID"],
    "redirect_uri": os.environ["ALPACA_OAUTH_REDIRECT_URI"],
    "scope": "account:write trading",
    "state": secrets.token_urlsafe(24),
}
authorize_url = "https://app.alpaca.markets/oauth/authorize?" + urlencode(params)
```

After the user approves, Alpaca redirects to your `redirect_uri` with:
- `code` — short-lived authorization code (use immediately; codes expire quickly)
- `state` — echoed back so you can verify it

---

## 2. Token Exchange

Exchange the authorization code for an access token via a POST to:

```
POST https://api.alpaca.markets/oauth/token
Content-Type: application/x-www-form-urlencoded
```

### Request body (form-encoded)

| Field          | Value / Description                              |
|----------------|--------------------------------------------------|
| `grant_type`   | `authorization_code`                             |
| `code`         | The authorization code received in the callback  |
| `client_id`    | Your OAuth app client ID                         |
| `client_secret`| Your OAuth app client secret                     |
| `redirect_uri` | Must exactly match the registered redirect URI   |

### Response JSON

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "scope": "account:write trading"
}
```

| Field          | Description                                                          |
|----------------|----------------------------------------------------------------------|
| `access_token` | The token to pass to `TradingClient(oauth_token=...)`                |
| `token_type`   | Always `"Bearer"`                                                    |
| `scope`        | The scopes actually granted (may be a subset of what was requested)  |

### Refresh tokens

**Alpaca does NOT issue refresh tokens** in its standard Connect OAuth flow. The
`access_token` is long-lived but has no explicit `expires_in` field in the token
response. Store the token securely and treat it as valid until the user explicitly
revokes it or you call the revocation endpoint.

> **Verification note:** The alpaca-py SDK source (`alpaca/common/rest.py`) contains
> no refresh-token logic — `_get_auth_headers()` simply uses the static bearer token.
> GitHub search of the repo for "oauth token refresh" returns zero results, consistent
> with no refresh-token support. The plan's note ("typically does NOT issue refresh
> tokens") matches observed current behavior.

### Example

```python
import httpx

def exchange_code(code: str) -> dict:
    r = httpx.post(
        "https://api.alpaca.markets/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": os.environ["ALPACA_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["ALPACA_OAUTH_CLIENT_SECRET"],
            "redirect_uri": os.environ["ALPACA_OAUTH_REDIRECT_URI"],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()  # {"access_token": "...", "token_type": "Bearer", "scope": "..."}
```

---

## 3. Token Revocation

To revoke an issued access token, POST to:

```
POST https://api.alpaca.markets/oauth/revoke
Content-Type: application/x-www-form-urlencoded
```

### Request body

| Field           | Description                       |
|-----------------|-----------------------------------|
| `token`         | The access token to revoke        |
| `client_id`     | Your OAuth app client ID          |
| `client_secret` | Your OAuth app client secret      |

### Example

```python
def revoke_token(access_token: str) -> None:
    r = httpx.post(
        "https://api.alpaca.markets/oauth/revoke",
        data={
            "token": access_token,
            "client_id": os.environ["ALPACA_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["ALPACA_OAUTH_CLIENT_SECRET"],
        },
        timeout=30,
    )
    r.raise_for_status()
```

A successful revocation returns HTTP 200 with an empty body or `{}`.

---

## 4. Using the Access Token with alpaca-py

Pass the token to `TradingClient` via the `oauth_token` parameter instead of
`api_key`/`secret_key`. The SDK sends `Authorization: Bearer <token>` on every request.

```python
from alpaca.trading.client import TradingClient

def client_for_user(access_token: str, paper: bool = False) -> TradingClient:
    """Return a TradingClient authenticated with an OAuth access token."""
    return TradingClient(oauth_token=access_token, paper=paper)

# Usage
client = client_for_user(access_token)
account = client.get_account()
print(account.id, account.status, account.cash)
```

**Constructor signature (oauth variant):**

```python
TradingClient(
    oauth_token: Optional[str] = None,  # use this instead of api_key/secret_key
    paper: bool = True,
    raw_data: bool = False,
    url_override: Optional[str] = None,
)
```

The SDK enforces mutual exclusivity: supplying `oauth_token` together with
`api_key`/`secret_key` raises a validation error.

When the token is scoped to `trading`, the client can place and cancel orders and manage
positions. Read-only account data is available with `account:write`. The `data` scope
is separate and rarely needed via OAuth (use direct API keys for market data instead).

---

## 5. Scopes

| Scope           | What it allows                                             |
|-----------------|------------------------------------------------------------|
| `account:write` | Read account info, balances, portfolio history; modify settings |
| `trading`       | Submit, cancel, replace orders; close positions            |
| `data`          | Access market data endpoints on behalf of the user         |

Request only the scopes your app actually needs. Alpaca shows the user the requested
scopes on the consent page.

---

## 6. Common Errors

| Error code            | Cause                                                                   |
|-----------------------|-------------------------------------------------------------------------|
| `invalid_grant`       | Authorization code expired, already used, or does not match `redirect_uri` |
| `invalid_client`      | `client_id` or `client_secret` is wrong                                |
| `unauthorized_client` | The client is not authorized to use this grant type or the requested scopes were not approved |
| `invalid_request`     | Missing or malformed required parameter (e.g. `grant_type` absent)     |

Error responses follow the standard OAuth 2.0 format:

```json
{
  "error": "invalid_grant",
  "error_description": "..."
}
```

HTTP status is 400 for client errors; raise on non-2xx and inspect the body.
