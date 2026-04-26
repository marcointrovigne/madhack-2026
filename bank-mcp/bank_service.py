from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import os
import random
import sqlite3
from threading import RLock
from typing import List, Optional


VALID_POLICIES = frozenset({"capital_preservation", "balanced", "yield_seeking"})
MAIN_COMPANY_CLIENT_ID = "main-company"


class MockBankService:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._lock = RLock()
        self._is_new_db_file = not os.path.exists(db_path)
        self._init_db()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _parse_amount(value: str | float | int | Decimal) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid amount.")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return amount.quantize(Decimal("0.01"))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bank_clients (
                    client_id TEXT PRIMARY KEY,
                    bank_account_ref TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    balance TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS company_policies (
                    client_id TEXT PRIMARY KEY,
                    policy TEXT NOT NULL DEFAULT 'balanced',
                    operating_reserve TEXT NOT NULL DEFAULT '0.00',
                    reinvestment_reserve TEXT NOT NULL DEFAULT '0.00',
                    target_allocation_json TEXT,
                    dca_amount TEXT NOT NULL DEFAULT '0.00',
                    dca_cadence TEXT NOT NULL DEFAULT 'off',
                    broker_account_id TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bank_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    movement_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    balance_after TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    description TEXT NOT NULL,
                    counterparty TEXT,
                    happened_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bank_movements_client_time
                ON bank_movements(client_id, happened_at DESC)
                """
            )
            conn.commit()

    @staticmethod
    def _row_to_payload(row: sqlite3.Row) -> dict:
        return {
            "client_id": row["client_id"],
            "bank_account_ref": row["bank_account_ref"],
            "currency": row["currency"],
            "balance": row["balance"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _movement_row_to_payload(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "client_id": row["client_id"],
            "movement_type": row["movement_type"],
            "category": row["category"],
            "amount": row["amount"],
            "balance_after": row["balance_after"],
            "currency": row["currency"],
            "description": row["description"],
            "counterparty": row["counterparty"],
            "happened_at": row["happened_at"],
            "created_at": row["created_at"],
        }

    def _record_movement(
        self,
        conn: sqlite3.Connection,
        *,
        client_id: str,
        movement_type: str,
        category: str,
        amount: Decimal,
        balance_after: Decimal,
        currency: str = "USD",
        description: str,
        counterparty: Optional[str] = None,
        happened_at: Optional[str] = None,
    ):
        now = self._now_iso()
        conn.execute(
            """
            INSERT INTO bank_movements (
                client_id, movement_type, category, amount, balance_after, currency,
                description, counterparty, happened_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                movement_type,
                category,
                str(amount.quantize(Decimal("0.01"))),
                str(balance_after.quantize(Decimal("0.01"))),
                currency,
                description,
                counterparty,
                happened_at or now,
                now,
            ),
        )

    def ensure_client(self, client_id: str, opening_balance: str | float | int | Decimal) -> dict:
        if not client_id or not client_id.strip():
            raise ValueError("Client id is required.")

        normalized_id = client_id.strip()
        amount = self._parse_amount(opening_balance) if str(opening_balance) != "0" else Decimal("0.00")

        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (normalized_id,),
            ).fetchone()
            if existing:
                return self._row_to_payload(existing)

            conn.execute(
                """
                INSERT INTO bank_clients (client_id, bank_account_ref, currency, balance, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    normalized_id,
                    f"mock-bank-{normalized_id}",
                    "USD",
                    str(amount),
                    self._now_iso(),
                ),
            )
            conn.commit()

            inserted = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (normalized_id,),
            ).fetchone()
            return self._row_to_payload(inserted)

    def list_clients(self) -> List[dict]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM bank_clients ORDER BY client_id").fetchall()
            return [self._row_to_payload(r) for r in rows]

    def get_client(self, client_id: str) -> dict:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (client_id.strip(),),
            ).fetchone()
            if not row:
                raise ValueError(f"Client '{client_id}' not found.")
            return self._row_to_payload(row)

    def deposit(self, client_id: str, amount: str | float | int | Decimal) -> dict:
        delta = self._parse_amount(amount)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (client_id.strip(),),
            ).fetchone()
            if not row:
                raise ValueError(f"Client '{client_id}' not found.")

            updated = Decimal(row["balance"]) + delta
            conn.execute(
                "UPDATE bank_clients SET balance = ? WHERE client_id = ?",
                (str(updated), row["client_id"]),
            )
            self._record_movement(
                conn,
                client_id=row["client_id"],
                movement_type="incoming",
                category="deposit",
                amount=delta,
                balance_after=updated,
                description="Deposit received",
            )
            conn.commit()
            updated_row = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (row["client_id"],),
            ).fetchone()
            return self._row_to_payload(updated_row)

    def withdraw(self, client_id: str, amount: str | float | int | Decimal) -> dict:
        delta = self._parse_amount(amount)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (client_id.strip(),),
            ).fetchone()
            if not row:
                raise ValueError(f"Client '{client_id}' not found.")

            current = Decimal(row["balance"])
            if current < delta:
                raise ValueError("Insufficient balance.")

            updated = current - delta
            conn.execute(
                "UPDATE bank_clients SET balance = ? WHERE client_id = ?",
                (str(updated), row["client_id"]),
            )
            self._record_movement(
                conn,
                client_id=row["client_id"],
                movement_type="spending",
                category="withdrawal",
                amount=delta,
                balance_after=updated,
                description="Withdrawal",
            )
            conn.commit()
            updated_row = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (row["client_id"],),
            ).fetchone()
            return self._row_to_payload(updated_row)

    def transfer(self, from_client_id: str, to_client_id: str, amount: str | float | int | Decimal):
        delta = self._parse_amount(amount)
        from_id = from_client_id.strip()
        to_id = to_client_id.strip()
        if from_id == to_id:
            raise ValueError("Source and destination clients must be different.")

        with self._lock, self._connect() as conn:
            source = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (from_id,),
            ).fetchone()
            destination = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (to_id,),
            ).fetchone()
            if not source:
                raise ValueError(f"Client '{from_id}' not found.")
            if not destination:
                raise ValueError(f"Client '{to_id}' not found.")

            source_balance = Decimal(source["balance"])
            destination_balance = Decimal(destination["balance"])
            if source_balance < delta:
                raise ValueError("Insufficient balance.")

            conn.execute(
                "UPDATE bank_clients SET balance = ? WHERE client_id = ?",
                (str(source_balance - delta), from_id),
            )
            conn.execute(
                "UPDATE bank_clients SET balance = ? WHERE client_id = ?",
                (str(destination_balance + delta), to_id),
            )
            self._record_movement(
                conn,
                client_id=from_id,
                movement_type="spending",
                category="transfer_out",
                amount=delta,
                balance_after=source_balance - delta,
                description=f"Transfer to {to_id}",
                counterparty=to_id,
            )
            self._record_movement(
                conn,
                client_id=to_id,
                movement_type="incoming",
                category="transfer_in",
                amount=delta,
                balance_after=destination_balance + delta,
                description=f"Transfer from {from_id}",
                counterparty=from_id,
            )
            conn.commit()

            source_after = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (from_id,),
            ).fetchone()
            destination_after = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (to_id,),
            ).fetchone()
            return self._row_to_payload(source_after), self._row_to_payload(destination_after)

    @staticmethod
    def _policy_row_to_payload(row: sqlite3.Row) -> dict:
        return {
            "client_id": row["client_id"],
            "policy": row["policy"],
            "operating_reserve": row["operating_reserve"],
            "reinvestment_reserve": row["reinvestment_reserve"],
            "target_allocation_json": row["target_allocation_json"],
            "dca_amount": row["dca_amount"],
            "dca_cadence": row["dca_cadence"],
            "broker_account_id": row["broker_account_id"],
            "updated_at": row["updated_at"],
        }

    def _parse_non_negative_amount(self, value: str | float | int | Decimal) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid amount.")
        if amount < 0:
            raise ValueError("Amount must be non-negative.")
        return amount.quantize(Decimal("0.01"))

    def upsert_company_policy(
        self,
        client_id: str,
        policy: str,
        operating_reserve: str | float | int | Decimal,
        reinvestment_reserve: str | float | int | Decimal,
        target_allocation_json: Optional[str] = None,
        dca_amount: str | float | int | Decimal = 0,
        dca_cadence: str = "off",
        broker_account_id: Optional[str] = None,
    ) -> dict:
        cid = client_id.strip()
        if not cid:
            raise ValueError("Client id is required.")
        pol = policy.strip().lower()
        if pol not in VALID_POLICIES:
            raise ValueError(
                f"Invalid policy '{policy}'. Expected one of: {', '.join(sorted(VALID_POLICIES))}."
            )
        op = self._parse_non_negative_amount(operating_reserve)
        rein = self._parse_non_negative_amount(reinvestment_reserve)
        dca = self._parse_non_negative_amount(dca_amount)
        cadence = (dca_cadence or "off").strip().lower() or "off"
        now = self._now_iso()
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT client_id FROM bank_clients WHERE client_id = ?", (cid,)).fetchone()
            if not row:
                raise ValueError(f"Company bank client '{cid}' not found. Create the client first.")
            existing = conn.execute(
                "SELECT client_id FROM company_policies WHERE client_id = ?", (cid,)
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE company_policies SET
                        policy = ?,
                        operating_reserve = ?,
                        reinvestment_reserve = ?,
                        target_allocation_json = ?,
                        dca_amount = ?,
                        dca_cadence = ?,
                        broker_account_id = COALESCE(?, broker_account_id),
                        updated_at = ?
                    WHERE client_id = ?
                    """,
                    (
                        pol,
                        str(op),
                        str(rein),
                        target_allocation_json,
                        str(dca),
                        cadence,
                        broker_account_id,
                        now,
                        cid,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO company_policies (
                        client_id, policy, operating_reserve, reinvestment_reserve,
                        target_allocation_json, dca_amount, dca_cadence, broker_account_id, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cid,
                        pol,
                        str(op),
                        str(rein),
                        target_allocation_json,
                        str(dca),
                        cadence,
                        broker_account_id,
                        now,
                    ),
                )
            conn.commit()
            out = conn.execute(
                "SELECT * FROM company_policies WHERE client_id = ?", (cid,)
            ).fetchone()
            return self._policy_row_to_payload(out)

    def get_company_policy(self, client_id: str) -> dict:
        cid = client_id.strip()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM company_policies WHERE client_id = ?", (cid,)
            ).fetchone()
            if not row:
                raise ValueError(f"No company policy for '{cid}'.")
            return self._policy_row_to_payload(row)

    def get_company_policy_or_none(self, client_id: str) -> Optional[dict]:
        try:
            return self.get_company_policy(client_id)
        except ValueError:
            return None

    def list_company_policies(self) -> List[dict]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM company_policies ORDER BY client_id"
            ).fetchall()
            return [self._policy_row_to_payload(r) for r in rows]

    def set_broker_account_id(self, client_id: str, broker_account_id: Optional[str]) -> dict:
        """Link company bank client_id to Alpaca Broker corporate account UUID."""
        cid = client_id.strip()
        now = self._now_iso()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT client_id FROM company_policies WHERE client_id = ?", (cid,)
            ).fetchone()
            if not row:
                raise ValueError(f"No company policy for '{cid}'. Set policy first.")
            conn.execute(
                """
                UPDATE company_policies SET broker_account_id = ?, updated_at = ?
                WHERE client_id = ?
                """,
                (broker_account_id, now, cid),
            )
            conn.commit()
            out = conn.execute(
                "SELECT * FROM company_policies WHERE client_id = ?", (cid,)
            ).fetchone()
            return self._policy_row_to_payload(out)

    def seed_mock_clients(self, total_clients: int = 250):
        with self._lock, self._connect() as conn:
            current_count = conn.execute("SELECT COUNT(*) AS count FROM bank_clients").fetchone()["count"]
            if current_count > 0:
                return

            now = self._now_iso()
            for index in range(1, total_clients + 1):
                client_id = f"client-{index:04d}"
                opening_balance = Decimal("1000.00") + Decimal(index * 37 % 9000)
                conn.execute(
                    """
                    INSERT INTO bank_clients (client_id, bank_account_ref, currency, balance, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        client_id,
                        f"mock-bank-{client_id}",
                        "USD",
                        str(opening_balance.quantize(Decimal("0.01"))),
                        now,
                    ),
                )
            conn.commit()

    def seed_demo_companies(self):
        """Owner-operator demo companies + treasury policies (idempotent)."""
        demo = [
            ("maria-studio", Decimal("35000.00"), "capital_preservation", Decimal("20000"), Decimal("10000")),
            ("dev-shop", Decimal("120000.00"), "balanced", Decimal("50000"), Decimal("25000")),
            ("design-co", Decimal("80000.00"), "yield_seeking", Decimal("15000"), Decimal("5000")),
        ]
        for client_id, opening_balance, policy, op_res, rein_res in demo:
            self.ensure_client(client_id, opening_balance)
            self.upsert_company_policy(
                client_id=client_id,
                policy=policy,
                operating_reserve=op_res,
                reinvestment_reserve=rein_res,
                target_allocation_json=None,
                dca_amount=0,
                dca_cadence="off",
                broker_account_id=None,
            )

    def list_movements(self, client_id: str, limit: int = 200, offset: int = 0) -> List[dict]:
        cid = client_id.strip()
        if not cid:
            raise ValueError("Client id is required.")
        safe_limit = max(1, min(limit, 1000))
        safe_offset = max(0, offset)
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM bank_movements
                WHERE client_id = ?
                ORDER BY happened_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (cid, safe_limit, safe_offset),
            ).fetchall()
            return [self._movement_row_to_payload(r) for r in rows]

    def get_statement(
        self, client_id: str, from_date: str, to_date: str, limit: int = 2000
    ) -> dict:
        cid = client_id.strip()
        if not cid:
            raise ValueError("Client id is required.")
        try:
            start = datetime.fromisoformat(from_date).date()
            end = datetime.fromisoformat(to_date).date()
        except ValueError:
            raise ValueError("Dates must be ISO format, e.g. 2026-04-26.")
        if end < start:
            raise ValueError("to_date must be on or after from_date.")

        start_ts = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        end_ts = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).isoformat()

        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM bank_movements
                WHERE client_id = ? AND happened_at >= ? AND happened_at < ?
                ORDER BY happened_at ASC, id ASC
                LIMIT ?
                """,
                (cid, start_ts, end_ts, max(1, min(limit, 10000))),
            ).fetchall()
            movements = [self._movement_row_to_payload(r) for r in rows]

        total_incoming = sum(
            Decimal(m["amount"]) for m in movements if m["movement_type"] == "incoming"
        ).quantize(Decimal("0.01"))
        total_spending = sum(
            Decimal(m["amount"]) for m in movements if m["movement_type"] == "spending"
        ).quantize(Decimal("0.01"))

        return {
            "client_id": cid,
            "from_date": from_date,
            "to_date": to_date,
            "movement_count": len(movements),
            "total_incoming": str(total_incoming),
            "total_spending": str(total_spending),
            "net_flow": str((total_incoming - total_spending).quantize(Decimal("0.01"))),
            "movements": movements,
        }

    def seed_main_company_history(self, years: int = 3):
        seed = self._load_main_seed_config()
        client_id = seed.get("client_id", MAIN_COMPANY_CLIENT_ID)
        opening_balance = Decimal(str(seed.get("opening_balance", "325000.00")))
        reserve_operating = Decimal(str(seed.get("operating_reserve", "180000.00")))
        reserve_reinvestment = Decimal(str(seed.get("reinvestment_reserve", "60000.00")))
        dca_amount = Decimal(str(seed.get("dca_amount", "15000.00")))
        policy = str(seed.get("policy", "balanced"))
        min_guard_balance = Decimal(str(seed.get("min_guard_balance", "85000.00")))
        daily_revenue_min = int(seed.get("daily_revenue_min", 2200))
        daily_revenue_max = int(seed.get("daily_revenue_max", 11500))
        daily_ops_min = int(seed.get("daily_ops_min", 900))
        daily_ops_max = int(seed.get("daily_ops_max", 4800))
        payroll_min = int(seed.get("payroll_min", 26000))
        payroll_max = int(seed.get("payroll_max", 48000))
        tax_min = int(seed.get("tax_min", 12000))
        tax_max = int(seed.get("tax_max", 30000))
        financing_min = int(seed.get("financing_min", 150000))
        financing_max = int(seed.get("financing_max", 350000))
        safeguard_min = int(seed.get("safeguard_min", 90000))
        safeguard_max = int(seed.get("safeguard_max", 180000))
        random_seed = int(seed.get("random_seed", 26))

        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT COUNT(*) AS count FROM bank_movements WHERE client_id = ?",
                (client_id,),
            ).fetchone()["count"]
            if existing > 0:
                return

            self.ensure_client(client_id, opening_balance)
            self.upsert_company_policy(
                client_id=client_id,
                policy=policy,
                operating_reserve=reserve_operating,
                reinvestment_reserve=reserve_reinvestment,
                dca_amount=dca_amount,
                dca_cadence="monthly",
            )

            client = conn.execute(
                "SELECT * FROM bank_clients WHERE client_id = ?",
                (client_id,),
            ).fetchone()
            balance = Decimal(client["balance"])

            today = date.today()
            start_date = today - timedelta(days=365 * years)
            rng = random.Random(random_seed)

            for day_idx in range((today - start_date).days + 1):
                d = start_date + timedelta(days=day_idx)
                day_base = datetime(d.year, d.month, d.day, 12, 0, tzinfo=timezone.utc)

                # Revenue settlements (B2B SaaS style): weekdays
                if d.weekday() < 5:
                    revenue = Decimal(rng.randint(daily_revenue_min, daily_revenue_max))
                    balance += revenue
                    self._record_movement(
                        conn,
                        client_id=client_id,
                        movement_type="incoming",
                        category="revenue",
                        amount=revenue,
                        balance_after=balance,
                        description="Customer invoice settlement",
                        counterparty="enterprise-customers",
                        happened_at=day_base.replace(hour=10, minute=15).isoformat(),
                    )

                # Operating spend, usually daily
                if rng.random() < 0.9:
                    ops = Decimal(rng.randint(daily_ops_min, daily_ops_max))
                    balance -= ops
                    self._record_movement(
                        conn,
                        client_id=client_id,
                        movement_type="spending",
                        category="operating_expense",
                        amount=ops,
                        balance_after=balance,
                        description="Vendors, cloud and tools",
                        counterparty="ops-vendors",
                        happened_at=day_base.replace(hour=16, minute=40).isoformat(),
                    )

                # Payroll on 5th and 20th
                if d.day in {5, 20}:
                    payroll = Decimal(rng.randint(payroll_min, payroll_max))
                    balance -= payroll
                    self._record_movement(
                        conn,
                        client_id=client_id,
                        movement_type="spending",
                        category="payroll",
                        amount=payroll,
                        balance_after=balance,
                        description="Payroll batch",
                        counterparty="company-payroll",
                        happened_at=day_base.replace(hour=13, minute=0).isoformat(),
                    )

                # Tax & compliance monthly
                if d.day == 28:
                    tax = Decimal(rng.randint(tax_min, tax_max))
                    balance -= tax
                    self._record_movement(
                        conn,
                        client_id=client_id,
                        movement_type="spending",
                        category="tax",
                        amount=tax,
                        balance_after=balance,
                        description="Tax and regulatory payments",
                        counterparty="tax-authority",
                        happened_at=day_base.replace(hour=14, minute=20).isoformat(),
                    )

                # Quarterly financing/investor inflow
                if d.month in {1, 4, 7, 10} and d.day == 3:
                    financing = Decimal(rng.randint(financing_min, financing_max))
                    balance += financing
                    self._record_movement(
                        conn,
                        client_id=client_id,
                        movement_type="incoming",
                        category="financing",
                        amount=financing,
                        balance_after=balance,
                        description="Strategic capital contribution",
                        counterparty="investors",
                        happened_at=day_base.replace(hour=9, minute=30).isoformat(),
                    )

                # Keep balance realistic: auto overdraft protection inflow if needed
                if balance < min_guard_balance:
                    safeguard = Decimal(rng.randint(safeguard_min, safeguard_max))
                    balance += safeguard
                    self._record_movement(
                        conn,
                        client_id=client_id,
                        movement_type="incoming",
                        category="internal_treasury_buffer",
                        amount=safeguard,
                        balance_after=balance,
                        description="Internal treasury buffer transfer",
                        counterparty="group-treasury",
                        happened_at=day_base.replace(hour=18, minute=0).isoformat(),
                    )

            conn.execute(
                "UPDATE bank_clients SET balance = ? WHERE client_id = ?",
                (str(balance.quantize(Decimal("0.01"))), client_id),
            )
            conn.commit()

    def _load_main_seed_config(self) -> dict:
        seed_file = os.getenv(
            "BANK_MOCK_MAIN_SEED_FILE",
            os.path.join(os.path.dirname(__file__), "seeds", "main_company_seed.json"),
        )
        if not os.path.exists(seed_file):
            return {}
        with open(seed_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            raise ValueError("Main company seed file must contain a JSON object.")
        return payload


def build_service_from_env() -> MockBankService:
    db_path = os.getenv("BANK_MOCK_DB_PATH", "./data/bank_mock.sqlite3")
    seed_count = int(os.getenv("BANK_MOCK_SEED_COUNT", "250"))
    service = MockBankService(db_path=db_path)
    service.seed_mock_clients(total_clients=seed_count)
    if os.getenv("BANK_MOCK_SEED_DEMO_COMPANIES", "true").lower() in {"1", "true", "yes", "on"}:
        service.seed_demo_companies()
    if os.getenv("BANK_MOCK_SEED_MAIN_COMPANY", "true").lower() in {"1", "true", "yes", "on"}:
        if service._is_new_db_file:
            service.seed_main_company_history(
                years=int(os.getenv("BANK_MOCK_MAIN_COMPANY_HISTORY_YEARS", "3"))
            )
    return service
