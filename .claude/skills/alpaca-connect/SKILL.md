---
name: alpaca-connect
description: Use when building a third-party integration that lets users log in with their existing Alpaca account via OAuth2. Triggers include "Alpaca OAuth", "Connect API", "third-party Alpaca app", "log in with Alpaca", "Alpaca authorization flow", "Alpaca access token".
---

# Alpaca Connect API

Implement OAuth2 against Alpaca's Connect API in Python.

## When invoked

1. Confirm `alpaca-py` is installed (also requires `httpx` or `requests` — install if missing)
2. Confirm `ALPACA_OAUTH_CLIENT_ID` and `ALPACA_OAUTH_CLIENT_SECRET` are set, plus a registered `redirect_uri`
3. If the task matches a known pattern, read `references/recipes.md`
4. If the task needs protocol details, read `references/sdk-reference.md`
5. Live fallback: WebFetch `https://docs.alpaca.markets/docs/oauth-apps`

## Quick reference

- Authorize URL: `https://app.alpaca.markets/oauth/authorize`
- Token URL: `https://api.alpaca.markets/oauth/token`
- Scopes: `account:write`, `trading`, `data`
- Token exchange uses standard OAuth2 authorization-code grant
- Access tokens can be passed to `TradingClient(oauth_token=...)` instead of `api_key`/`secret_key`

## Files

- `references/auth-setup.md`
- `references/sdk-reference.md`
- `references/recipes.md`
- `scripts/check_setup.py`
