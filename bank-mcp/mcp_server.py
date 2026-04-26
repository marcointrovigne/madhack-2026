from mcp.server.fastmcp import FastMCP

from bank_service import build_service_from_env


mcp = FastMCP("bank-account-mock")
service = build_service_from_env()


@mcp.tool()
def health() -> dict:
    return {"status": "ok"}


@mcp.tool()
def list_clients() -> dict:
    return {"clients": service.list_clients()}


@mcp.tool()
def create_client(client_id: str, opening_balance: float = 0) -> dict:
    return service.ensure_client(client_id=client_id, opening_balance=opening_balance)


@mcp.tool()
def get_client(client_id: str) -> dict:
    return service.get_client(client_id=client_id)


@mcp.tool()
def deposit(client_id: str, amount: float) -> dict:
    return service.deposit(client_id=client_id, amount=amount)


@mcp.tool()
def withdraw(client_id: str, amount: float) -> dict:
    return service.withdraw(client_id=client_id, amount=amount)


@mcp.tool()
def transfer(from_client_id: str, to_client_id: str, amount: float) -> dict:
    source, destination = service.transfer(
        from_client_id=from_client_id,
        to_client_id=to_client_id,
        amount=amount,
    )
    return {"from": source, "to": destination}


@mcp.tool()
def list_company_policies() -> dict:
    return {"policies": service.list_company_policies()}


@mcp.tool()
def get_company_policy(client_id: str) -> dict:
    return service.get_company_policy(client_id=client_id)


@mcp.tool()
def upsert_company_policy(
    client_id: str,
    policy: str,
    operating_reserve: float,
    reinvestment_reserve: float,
    target_allocation_json: str | None = None,
    dca_amount: float = 0,
    dca_cadence: str = "off",
    broker_account_id: str | None = None,
) -> dict:
    return service.upsert_company_policy(
        client_id=client_id,
        policy=policy,
        operating_reserve=operating_reserve,
        reinvestment_reserve=reinvestment_reserve,
        target_allocation_json=target_allocation_json,
        dca_amount=dca_amount,
        dca_cadence=dca_cadence,
        broker_account_id=broker_account_id,
    )


@mcp.tool()
def set_company_broker_account(client_id: str, broker_account_id: str | None = None) -> dict:
    return service.set_broker_account_id(client_id, broker_account_id)


@mcp.tool()
def list_movements(client_id: str, limit: int = 200, offset: int = 0) -> dict:
    return {
        "client_id": client_id,
        "limit": limit,
        "offset": offset,
        "movements": service.list_movements(client_id=client_id, limit=limit, offset=offset),
    }


@mcp.tool()
def get_statement(client_id: str, from_date: str, to_date: str, limit: int = 2000) -> dict:
    return service.get_statement(
        client_id=client_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )


if __name__ == "__main__":
    mcp.run()
