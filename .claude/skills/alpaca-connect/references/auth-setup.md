# Connect API — Auth & Setup

## OAuth app registration

Register an OAuth app at `https://app.alpaca.markets/oauth/apps`. You'll get:

- `client_id`
- `client_secret`
- A registered `redirect_uri` (e.g. `http://localhost:3000/callback` for dev)

## Environment variables

```
ALPACA_OAUTH_CLIENT_ID=your_client_id
ALPACA_OAUTH_CLIENT_SECRET=your_client_secret
ALPACA_OAUTH_REDIRECT_URI=http://localhost:3000/callback
```

## Endpoints

- Authorize: `https://app.alpaca.markets/oauth/authorize`
- Token exchange: `https://api.alpaca.markets/oauth/token`
- Revoke: `https://api.alpaca.markets/oauth/revoke`

## Scopes

- `account:write` — read + modify account
- `trading` — place/cancel orders, manage positions
- `data` — market data access (rarely needed; use direct keys for data)

## Default flow

Authorization-code grant. The app shows the user a consent page on Alpaca, then Alpaca redirects back to `redirect_uri` with a `code` query param, which the app trades for an access token + refresh token.
