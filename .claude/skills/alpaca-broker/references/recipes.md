# Broker API — Recipes

```python
import os
from alpaca.broker.client import BrokerClient

client = BrokerClient(
    api_key=os.environ["BROKER_API_KEY_ID"],
    secret_key=os.environ["BROKER_API_SECRET_KEY"],
    sandbox=True,
)
```

## 1. Create an account (KYC)

```python
from alpaca.broker.requests import CreateAccountRequest
from alpaca.broker.models import (
    Contact, Identity, Disclosures, Agreement,
)
from alpaca.broker.enums import (
    TaxIdType, FundingSource, AgreementType,
)

req = CreateAccountRequest(
    contact=Contact(
        email_address="alice@example.com",
        phone_number="+15551234567",
        street_address=["123 Main St"],
        city="San Francisco", state="CA",
        postal_code="94105", country="USA",
    ),
    identity=Identity(
        given_name="Alice", family_name="Doe",
        date_of_birth="1990-01-01",
        tax_id="123-45-6789", tax_id_type=TaxIdType.USA_SSN,
        country_of_citizenship="USA",
        country_of_birth="USA",
        country_of_tax_residence="USA",
        funding_source=[FundingSource.EMPLOYMENT_INCOME],
    ),
    disclosures=Disclosures(
        is_control_person=False,
        is_affiliated_exchange_or_finra=False,
        is_politically_exposed=False,
        immediate_family_exposed=False,
    ),
    agreements=[
        Agreement(agreement=AgreementType.CUSTOMER,
                  signed_at="2025-04-25T12:00:00Z",
                  ip_address="192.0.2.1"),
        Agreement(agreement=AgreementType.MARGIN,
                  signed_at="2025-04-25T12:00:00Z",
                  ip_address="192.0.2.1"),
    ],
)
account = client.create_account(req)
print(account.id, account.status)
```

## 2. Fund an account: ACH relationship + transfer

```python
from alpaca.broker.requests import (
    CreateACHRelationshipRequest, CreateACHTransferRequest,
)
from alpaca.broker.enums import (
    BankAccountType, TransferType, TransferDirection,
)

ach = client.create_ach_relationship_for_account(
    account_id=account.id,
    ach_data=CreateACHRelationshipRequest(
        account_owner_name="Alice Doe",
        bank_account_type=BankAccountType.CHECKING,
        bank_account_number="32131231abc",
        bank_routing_number="121000358",
    ),
)

transfer = client.create_transfer_for_account(
    account_id=account.id,
    transfer_data=CreateACHTransferRequest(
        transfer_type=TransferType.ACH,
        relationship_id=ach.id,
        amount="100",
        direction=TransferDirection.INCOMING,
    ),
)
print(transfer.id, transfer.status)
```

## 3. List, get, update accounts

```python
from alpaca.broker.requests import ListAccountsRequest, UpdateAccountRequest

accts = client.list_accounts(ListAccountsRequest(query=None))
print(len(accts))

acct = client.get_account_by_id(account.id)

client.update_account(account.id, UpdateAccountRequest(
    contact=Contact(email_address="alice2@example.com",
                    phone_number="+15551234567",
                    street_address=["123 Main St"],
                    city="SF", state="CA",
                    postal_code="94105", country="USA"),
))
```

## 4. Place an order on behalf of an end-user

```python
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

order = client.submit_order_for_account(
    account_id=account.id,
    order_data=MarketOrderRequest(
        symbol="AAPL", qty=1,
        side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
    ),
)
print(order.id, order.status)
```

## 5. Journal cash between accounts (round-ups, allowances)

```python
from alpaca.broker.requests import CreateJournalRequest
from alpaca.broker.enums import JournalEntryType

journal = client.create_journal(CreateJournalRequest(
    from_account=parent_account_id,
    to_account=child_account_id,
    entry_type=JournalEntryType.CASH,
    amount="5.00",
    description="Weekly allowance",
))
print(journal.id, journal.status)
```

## 6. Webhooks for account events

The Broker API can POST events to your URL. Wire it up in the dashboard, then handle:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/alpaca/webhook")
async def webhook(req: Request):
    event = await req.json()
    # event["event_type"] examples: "account.updated", "transfer.completed", "trade"
    # Validate the signature header per Alpaca docs before trusting payload
    print(event["event_type"], event.get("account_id"))
    return {"ok": True}
```

(Signature validation requires the webhook secret from the Broker dashboard — see Alpaca docs `https://docs.alpaca.markets/docs/webhook-events`.)
