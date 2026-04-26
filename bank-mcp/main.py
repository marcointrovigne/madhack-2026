from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from bank_service import build_service_from_env


class ClientCreateRequest(BaseModel):
    client_id: str = Field(min_length=1)
    opening_balance: float = 0


class AmountRequest(BaseModel):
    amount: float = Field(gt=0)


class TransferRequest(BaseModel):
    from_client_id: str = Field(min_length=1)
    to_client_id: str = Field(min_length=1)
    amount: float = Field(gt=0)


class CompanyPolicyUpsertRequest(BaseModel):
    policy: str = Field(min_length=1)
    operating_reserve: float = Field(ge=0)
    reinvestment_reserve: float = Field(ge=0)
    target_allocation_json: str | None = None
    dca_amount: float = Field(default=0, ge=0)
    dca_cadence: str = Field(default="off")
    broker_account_id: str | None = None


class BrokerAccountLinkRequest(BaseModel):
    broker_account_id: str | None = Field(default=None, description="Alpaca Broker account UUID or null to clear")


class StatementQueryParams(BaseModel):
    from_date: str = Field(description="ISO date YYYY-MM-DD")
    to_date: str = Field(description="ISO date YYYY-MM-DD")
    limit: int = Field(default=2000, ge=1, le=10000)


app = FastAPI(title="Bank Account Mock Service", version="0.1.0")
service = build_service_from_env()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/clients")
def list_clients():
    return {"clients": service.list_clients()}


@app.post("/clients")
def create_client(request: ClientCreateRequest):
    try:
        account = service.ensure_client(request.client_id, request.opening_balance)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return account


@app.get("/clients/{client_id}")
def get_client(client_id: str):
    try:
        account = service.get_client(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return account


@app.post("/clients/{client_id}/deposit")
def deposit(client_id: str, request: AmountRequest):
    try:
        account = service.deposit(client_id, request.amount)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return account


@app.post("/clients/{client_id}/withdraw")
def withdraw(client_id: str, request: AmountRequest):
    try:
        account = service.withdraw(client_id, request.amount)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return account


@app.post("/transfer")
def transfer(request: TransferRequest):
    try:
        source, destination = service.transfer(
            request.from_client_id, request.to_client_id, request.amount
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"from": source, "to": destination}


@app.get("/company-policies")
def list_company_policies():
    return {"policies": service.list_company_policies()}


@app.get("/company-policies/{client_id}")
def get_company_policy(client_id: str):
    try:
        return service.get_company_policy(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/company-policies/{client_id}")
def upsert_company_policy(client_id: str, request: CompanyPolicyUpsertRequest):
    try:
        return service.upsert_company_policy(
            client_id=client_id,
            policy=request.policy,
            operating_reserve=request.operating_reserve,
            reinvestment_reserve=request.reinvestment_reserve,
            target_allocation_json=request.target_allocation_json,
            dca_amount=request.dca_amount,
            dca_cadence=request.dca_cadence,
            broker_account_id=request.broker_account_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/company-policies/{client_id}/broker-account")
def patch_broker_account(client_id: str, request: BrokerAccountLinkRequest):
    try:
        return service.set_broker_account_id(client_id, request.broker_account_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/clients/{client_id}/movements")
def list_movements(client_id: str, limit: int = 200, offset: int = 0):
    try:
        return {
            "client_id": client_id,
            "limit": limit,
            "offset": offset,
            "movements": service.list_movements(client_id=client_id, limit=limit, offset=offset),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/clients/{client_id}/statement")
def get_statement(client_id: str, request: StatementQueryParams):
    try:
        return service.get_statement(
            client_id=client_id,
            from_date=request.from_date,
            to_date=request.to_date,
            limit=request.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
