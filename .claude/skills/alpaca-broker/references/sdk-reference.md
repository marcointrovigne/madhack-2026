# Broker API — SDK Reference

Source: `alpaca-py` SDK (`alpacahq/alpaca-py`). Re-pull live details via Context7 or WebFetch if method signatures differ from what's here.

> **Key difference from Trading/Market Data:** Broker uses separate credentials (`BROKER_API_KEY_ID`, `BROKER_API_SECRET_KEY`) and `sandbox=True` instead of `paper=True`.

---

## 1. BrokerClient

Central client for all Broker API operations.

```python
from alpaca.broker.client import BrokerClient

client = BrokerClient(
    api_key="YOUR_BROKER_API_KEY_ID",
    secret_key="YOUR_BROKER_API_SECRET_KEY",
    sandbox=True,        # True for sandbox, False for production
    # raw_data=False,    # return raw dicts instead of model objects
    # url_override=None, # override base URL
)
```

### Account methods

| Method | Description |
|--------|-------------|
| `create_account(account_data)` | Create a new brokerage account (KYC flow) |
| `get_account_by_id(account_id)` | Fetch a single account by UUID |
| `list_accounts(filter?)` | List all accounts, optionally filtered |
| `update_account(account_id, update_data)` | Update contact/identity on an account |
| `close_account(account_id)` | Close an account |
| `get_trade_account_by_id(account_id)` | Get trading-specific data for an account |

```python
from alpaca.broker.requests import ListAccountsRequest, UpdateAccountRequest

# List all accounts
accounts = client.list_accounts()
# or filtered
accounts = client.list_accounts(ListAccountsRequest(query="alice"))

# Get one account
acct = client.get_account_by_id("c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4")

# Get trade info (buying power, cash, etc.)
trade_acct = client.get_trade_account_by_id(account_id)
```

### ACH relationship methods

| Method | Description |
|--------|-------------|
| `create_ach_relationship_for_account(account_id, ach_data)` | Link a bank account via routing/account numbers |
| `get_ach_relationships_for_account(account_id)` | List all ACH relationships on an account |
| `delete_ach_relationship_for_account(account_id, ach_relationship_id)` | Remove an ACH relationship |

```python
from alpaca.broker.requests import CreateACHRelationshipRequest
from alpaca.broker.enums import BankAccountType

ach = client.create_ach_relationship_for_account(
    account_id=account.id,
    ach_data=CreateACHRelationshipRequest(
        account_owner_name="Alice Doe",
        bank_account_type=BankAccountType.CHECKING,
        bank_account_number="32131231abc",
        bank_routing_number="121000358",
    ),
)

relationships = client.get_ach_relationships_for_account(account_id=account.id)
client.delete_ach_relationship_for_account(account_id=account.id, ach_relationship_id=ach.id)
```

### Transfer methods

| Method | Description |
|--------|-------------|
| `create_transfer_for_account(account_id, transfer_data)` | Initiate an ACH or wire transfer |
| `get_transfers_for_account(account_id, filter?)` | List transfers (returns iterator) |
| `cancel_transfer_for_account(account_id, transfer_id)` | Cancel a pending transfer |

```python
from alpaca.broker.requests import CreateACHTransferRequest
from alpaca.broker.enums import TransferType, TransferDirection

transfer = client.create_transfer_for_account(
    account_id=account.id,
    transfer_data=CreateACHTransferRequest(
        transfer_type=TransferType.ACH,
        relationship_id=ach.id,
        amount="100",
        direction=TransferDirection.INCOMING,
    ),
)

transfers = list(client.get_transfers_for_account(account_id=account.id))
client.cancel_transfer_for_account(account_id=account.id, transfer_id=transfer.id)
```

### Journal methods

| Method | Description |
|--------|-------------|
| `create_journal(journal_data)` | Transfer cash or securities between accounts |
| `create_batch_journal(batch_data)` | Transfer to/from multiple accounts at once |
| `get_journals(filter?)` | List journals |
| `get_journal_by_id(journal_id)` | Fetch a single journal |
| `cancel_journal_by_id(journal_id)` | Cancel a pending journal |

```python
from alpaca.broker.requests import CreateJournalRequest
from alpaca.broker.enums import JournalEntryType

journal = client.create_journal(CreateJournalRequest(
    from_account="c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4",
    to_account="0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
    entry_type=JournalEntryType.CASH,   # CASH = JNLC, SECURITY = JNLS
    amount=50,
))
```

### Trading on behalf of an account

| Method | Description |
|--------|-------------|
| `submit_order_for_account(account_id, order_data)` | Place an order for a customer account |
| `get_orders_for_account(account_id, filter?)` | List orders for an account |
| `get_order_for_account_by_id(account_id, order_id)` | Get a specific order |
| `cancel_orders_for_account(account_id)` | Cancel all open orders |
| `cancel_order_for_account_by_id(account_id, order_id)` | Cancel a specific order |
| `replace_order_for_account_by_id(account_id, order_id, order_data)` | Replace an order |
| `get_all_positions_for_account(account_id)` | List all open positions |
| `get_open_position_for_account(account_id, symbol_or_asset_id)` | Get a single position |
| `close_all_positions_for_account(account_id, cancel_orders?)` | Close all positions |
| `close_position_for_account(account_id, symbol_or_asset_id, close_options?)` | Close one position |

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

positions = client.get_all_positions_for_account(account_id=account.id)
```

### Documents and activities

| Method | Description |
|--------|-------------|
| `get_trade_documents_for_account(account_id, filter?)` | List trade documents (statements, confirmations) |
| `get_trade_document_for_account_by_id(account_id, document_id)` | Fetch document metadata |
| `download_trade_document_for_account_by_id(account_id, document_id)` | Download document bytes |
| `get_account_activities(filter?)` | Get trade/non-trade activities across accounts |

```python
from alpaca.broker.requests import GetAccountActivitiesRequest

activities = client.get_account_activities(GetAccountActivitiesRequest(
    account_id=account.id,
))
```

---

## 2. Account Creation Request Models

All classes below live in `alpaca.broker.requests` (for `CreateAccountRequest`) and `alpaca.broker.models` (for sub-models).

### CreateAccountRequest

```python
from alpaca.broker.requests import CreateAccountRequest

CreateAccountRequest(
    contact: Contact,                     # required
    identity: Identity,                   # required
    disclosures: Disclosures,             # required
    agreements: list[Agreement],          # required — must include at minimum CUSTOMER
    documents: list[AccountDocument] | None = None,
    trusted_contact: TrustedContact | None = None,
    account_type: AccountType | None = None,  # default: TRADING
)
```

### Contact

```python
from alpaca.broker.models import Contact

Contact(
    email_address: str,                   # required — unique across accounts
    phone_number: str,                    # required, e.g. "+15551234567"
    street_address: list[str],            # required, e.g. ["123 Main St"]
    city: str,                            # required
    state: str | None = None,             # required for USA
    postal_code: str | None = None,       # required for USA
    country: str,                         # required, ISO 3166-1 alpha-3, e.g. "USA"
)
```

### Identity

```python
from alpaca.broker.models import Identity
from alpaca.broker.enums import TaxIdType, FundingSource

Identity(
    given_name: str,                      # required — first name
    middle_name: str | None = None,
    family_name: str,                     # required — last name
    date_of_birth: str,                   # required, e.g. "1990-01-01"
    tax_id: str | None = None,            # SSN/ITIN/etc. (required for USA residents)
    tax_id_type: TaxIdType | None = None, # required if tax_id provided
    country_of_citizenship: str | None = None,
    country_of_birth: str | None = None,
    country_of_tax_residence: str,        # required, ISO 3166-1 alpha-3
    funding_source: list[FundingSource],  # required
    # Optional employment fields:
    annual_income_min: float | None = None,
    annual_income_max: float | None = None,
    liquid_net_worth_min: float | None = None,
    liquid_net_worth_max: float | None = None,
    total_net_worth_min: float | None = None,
    total_net_worth_max: float | None = None,
)
```

### Disclosures

```python
from alpaca.broker.models import Disclosures

Disclosures(
    is_control_person: bool,              # required — 10%+ ownership in a public company?
    is_affiliated_exchange_or_finra: bool, # required
    is_politically_exposed: bool,         # required
    immediate_family_exposed: bool,       # required
    # Optional:
    context: list | None = None,
)
```

### Agreement

```python
from alpaca.broker.models import Agreement
from alpaca.broker.enums import AgreementType

Agreement(
    agreement: AgreementType,             # required — see enum below
    signed_at: str,                       # required, ISO 8601 datetime string
    ip_address: str,                      # required — user's IP at signing
    revision: str | None = None,
)
```

### TrustedContact

```python
from alpaca.broker.models import TrustedContact

TrustedContact(
    given_name: str,
    family_name: str,
    email_address: str | None = None,
    phone_number: str | None = None,
    street_address: list[str] | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    country: str | None = None,
)
```

---

## 3. Funding Request Models

### CreateACHRelationshipRequest

```python
from alpaca.broker.requests import CreateACHRelationshipRequest
from alpaca.broker.enums import BankAccountType

CreateACHRelationshipRequest(
    account_owner_name: str,              # required — name on the bank account
    bank_account_type: BankAccountType,   # required — CHECKING or SAVINGS
    bank_account_number: str,             # required — bank account number
    bank_routing_number: str,             # required — ABA routing number
    nickname: str | None = None,
)
```

### CreatePlaidRelationshipRequest (Plaid integration)

```python
from alpaca.broker.requests import CreatePlaidRelationshipRequest

CreatePlaidRelationshipRequest(
    processor_token: str,                 # required — Plaid processor token
)

# Usage
ach = client.create_ach_relationship_for_account(
    account_id=account.id,
    ach_data=CreatePlaidRelationshipRequest(processor_token="processor-sandbox-..."),
)
```

### CreateACHTransferRequest

```python
from alpaca.broker.requests import CreateACHTransferRequest
from alpaca.broker.enums import TransferType, TransferDirection

CreateACHTransferRequest(
    transfer_type: TransferType,          # required — TransferType.ACH
    relationship_id: UUID | str,          # required — ACH relationship ID
    amount: str | float,                  # required — dollar amount, e.g. "100.00"
    direction: TransferDirection,         # required — INCOMING (deposit) or OUTGOING (withdrawal)
    # Optional:
    timing: TransferTiming | None = None,
    fee_payment_method: FeePaymentMethod | None = None,
)
```

### CreateBankRequest (International wire)

```python
from alpaca.broker.requests import CreateBankRequest
from alpaca.broker.enums import IdentifierType

CreateBankRequest(
    name: str,                            # required — name on bank account
    bank_code_type: IdentifierType,       # required — ABA or BIC
    bank_code: str,                       # required — routing number or BIC/SWIFT
    account_number: str,                  # required
    country: str | None = None,
)
```

### CreateBankTransferRequest

```python
from alpaca.broker.requests import CreateBankTransferRequest
from alpaca.broker.enums import TransferType, TransferDirection

CreateBankTransferRequest(
    transfer_type: TransferType,          # required — TransferType.WIRE
    bank_id: UUID | str,                  # required — bank ID from create_bank_for_account
    amount: str | float,                  # required
    direction: TransferDirection,         # required
    # Optional:
    additional_information: str | None = None,
)
```

---

## 4. Journal Request Model

### CreateJournalRequest

```python
from alpaca.broker.requests import CreateJournalRequest
from alpaca.broker.enums import JournalEntryType

CreateJournalRequest(
    from_account: UUID | str,             # required — source account ID
    to_account: UUID | str,               # required — destination account ID
    entry_type: JournalEntryType,         # required — CASH or SECURITY
    # For cash journals (entry_type=JournalEntryType.CASH):
    amount: float | str | None = None,
    # For security journals (entry_type=JournalEntryType.SECURITY):
    symbol: str | None = None,
    qty: float | None = None,
    # Optional:
    description: str | None = None,
)

# Cash journal
journal = client.create_journal(CreateJournalRequest(
    from_account="from-account-uuid",
    to_account="to-account-uuid",
    entry_type=JournalEntryType.CASH,     # wire: value = "JNLC"
    amount=50,
    description="Monthly allowance",
))

# Security journal
journal = client.create_journal(CreateJournalRequest(
    from_account="from-account-uuid",
    to_account="to-account-uuid",
    entry_type=JournalEntryType.SECURITY,  # wire: value = "JNLS"
    symbol="AAPL",
    qty=2,
))
```

---

## 5. Enums

All enums live in `alpaca.broker.enums`.

### AccountStatus

Returned on account objects — not an enum you set; it changes as the account moves through KYC.

```python
# Common values (string):
# "SUBMITTED"     — application received
# "APPROVAL_PENDING" — under review
# "APPROVED"      — approved but not yet active
# "ACTIVE"        — fully active, can trade
# "REJECTED"      — KYC failed
# "ACCOUNT_CLOSED"— closed
```

### TaxIdType

```python
from alpaca.broker.enums import TaxIdType

TaxIdType.USA_SSN          # U.S. Social Security Number
TaxIdType.USA_ITIN         # U.S. Individual Taxpayer Identification Number
TaxIdType.PASSPORT
TaxIdType.NATIONAL_ID
TaxIdType.DRIVER_LICENSE
TaxIdType.OTHER_GOV_ID
# + many country-specific values: ARG_AR_CUIT, BRA_CPF, GBR_UTR, etc.
```

### FundingSource

```python
from alpaca.broker.enums import FundingSource

FundingSource.EMPLOYMENT_INCOME   # "employment_income"
FundingSource.INVESTMENTS         # "investments"
FundingSource.INHERITANCE         # "inheritance"
FundingSource.BUSINESS_INCOME     # "business_income"
FundingSource.SAVINGS             # "savings"
FundingSource.FAMILY              # "family"
```

### AgreementType

> **Note:** In `alpaca-py`, the enum member names are SHORT (MARGIN, ACCOUNT, CUSTOMER, CRYPTO), not the long form shown in some docs.

```python
from alpaca.broker.enums import AgreementType

AgreementType.MARGIN      # "margin_agreement"
AgreementType.ACCOUNT     # "account_agreement"
AgreementType.CUSTOMER    # "customer_agreement"
AgreementType.CRYPTO      # "crypto_agreement"
AgreementType.OPTIONS     # "options_agreement"
```

### BankAccountType

```python
from alpaca.broker.enums import BankAccountType

BankAccountType.CHECKING   # "CHECKING"
BankAccountType.SAVINGS    # "SAVINGS"
```

### TransferType

```python
from alpaca.broker.enums import TransferType

TransferType.ACH    # "ach" — domestic US ACH transfers
TransferType.WIRE   # "wire" — international / domestic wire
```

### TransferDirection

```python
from alpaca.broker.enums import TransferDirection

TransferDirection.INCOMING   # "INCOMING" — deposit into the account
TransferDirection.OUTGOING   # "OUTGOING" — withdrawal from the account
```

### JournalEntryType

> **Note:** The enum member names are `CASH` and `SECURITY` in `alpaca-py`; they map to the API wire values `JNLC` and `JNLS`.

```python
from alpaca.broker.enums import JournalEntryType

JournalEntryType.CASH      # wire value: "JNLC" — cash journal
JournalEntryType.SECURITY  # wire value: "JNLS" — security (stock) journal
```

### JournalStatus

```python
from alpaca.broker.enums import JournalStatus

JournalStatus.QUEUED
JournalStatus.PENDING
JournalStatus.EXECUTED
JournalStatus.REJECTED
JournalStatus.CANCELED
JournalStatus.REFUSED
JournalStatus.CORRECT
JournalStatus.DELETED
```
