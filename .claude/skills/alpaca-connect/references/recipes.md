# Connect API — Recipes

## 1. Build the authorize URL

```python
import os, secrets
from urllib.parse import urlencode

CLIENT_ID = os.environ["ALPACA_OAUTH_CLIENT_ID"]
REDIRECT_URI = os.environ["ALPACA_OAUTH_REDIRECT_URI"]

def build_authorize_url(scopes: list[str]) -> tuple[str, str]:
    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": state,
    }
    url = "https://app.alpaca.markets/oauth/authorize?" + urlencode(params)
    return url, state
```

Store `state` in a session cookie / cache and verify it on callback.

## 2. Exchange code for access token

```python
import os, httpx

CLIENT_ID = os.environ["ALPACA_OAUTH_CLIENT_ID"]
CLIENT_SECRET = os.environ["ALPACA_OAUTH_CLIENT_SECRET"]
REDIRECT_URI = os.environ["ALPACA_OAUTH_REDIRECT_URI"]

def exchange_code(code: str) -> dict:
    r = httpx.post(
        "https://api.alpaca.markets/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()  # {"access_token": "...", "token_type": "Bearer", "scope": "..."}
```

## 3. Use the access token with alpaca-py

```python
from alpaca.trading.client import TradingClient

def client_for_user(access_token: str) -> TradingClient:
    return TradingClient(oauth_token=access_token, paper=False)

# example
client = client_for_user(token)
print(client.get_account().id)
```

## 4. FastAPI endpoint glue

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()
SESSIONS: dict[str, str] = {}  # state -> session_id, replace with real store

@app.get("/login")
def login():
    url, state = build_authorize_url(["account:write", "trading"])
    SESSIONS[state] = "user-session-id"
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str, state: str):
    if state not in SESSIONS:
        raise HTTPException(400, "bad state")
    SESSIONS.pop(state)
    token_data = exchange_code(code)
    # store token_data["access_token"] for the user
    return {"ok": True}
```
