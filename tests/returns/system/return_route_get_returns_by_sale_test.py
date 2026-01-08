import asyncio
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

chocolate_bar = {    
    "description": "Chocolate Bar",
    "barcode": "0123456789012",
    "price_per_unit": 2.99,
    "note": "Imported from Belgium",
    "quantity": 2
}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def client():
    from main import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def setup_database(event_loop):
    async def _reset():
        await reset() # Drop all tables
        await init_db() # Recreate all tables
    event_loop.run_until_complete(_reset())


@pytest.fixture(scope="function", autouse=True)
def auth_tokens(client, setup_database):
    """Authenticate users once and return their JWT tokens."""

    users = {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }

    tokens = {}
    for role, creds in users.items():
        response = client.post(BASE_URL + "/auth", json=creds)
        assert response.status_code == 200, f"Login failed for {role}"
        tokens[role] = f"Bearer {response.json()['token']}"
    tokens["unauthorized"] = ""
    return tokens


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}


@pytest.fixture
def return_creation(client, auth_tokens):

    # Reset balance
    balance_resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(auth_tokens, "admin")
    )
    assert balance_resp.status_code == 205

    # Add product
    product_resp = client.post(
        BASE_URL + "/products",
        headers=auth_header(auth_tokens, "admin"),
        json=chocolate_bar
    )
    assert product_resp.status_code == 201
    product_barcode = product_resp.json()["barcode"]

    # Create sale
    sale_resp = client.post(
        BASE_URL + "/sales",
        headers=auth_header(auth_tokens, "admin")
    )
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    add_prod_resp = client.post(
        BASE_URL + f"/sales/{sale_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={ "barcode": product_barcode, "amount": 2 }
    )

    assert add_prod_resp.status_code == 201

    # Close sale
    close_sale_resp = client.patch(
        BASE_URL + f"/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "admin"),
    )
    assert close_sale_resp.status_code == 200

    # Pay sale
    pay_sale_resp = client.patch(
        BASE_URL + f"/sales/{sale_id}/pay",
        headers=auth_header(auth_tokens, "admin"),
        params={ "cash_amount": 6.0}
    )    
    assert pay_sale_resp.status_code == 200

    ret_creation_resp = client.post(
        BASE_URL + "/returns",
        params={"sale_id": sale_id},
        headers=auth_header(auth_tokens, "admin")
    )
    # Assert response
    assert ret_creation_resp.status_code == 201
    return int(sale_id)

# ---------------------------
# GET TRANSACTION BY SALE TESTS 
# ---------------------------

def test_get_returns_by_sale_success_authorized_users(client, auth_tokens,return_creation):
    for role in ["admin", "manager", "cashier"]:
        # Get returns
        resp = client.get(
            BASE_URL + f"/returns/sale/{return_creation}",
            headers=auth_header(auth_tokens, role)
        )

        print(return_creation)
        print(resp.json())
        # Assert response
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1
    

def test_get_returns_by_sale_unauthenticated(client, auth_tokens,return_creation):
    # Get returns
    resp = client.get(
        BASE_URL + f"/returns/sale/{return_creation}",
        headers=auth_header(auth_tokens, "unauthorized")
    )
    # Assert response
    assert resp.status_code == 401

def test_get_returns_by_sale_invalid_id(client, auth_tokens):
    for role in ["admin", "manager", "cashier"]:
        # Get returns
        resp = client.get(
            BASE_URL + "/returns/sale/-2",
            headers=auth_header(auth_tokens, role)
        )
        # Assert response
        assert resp.status_code == 400

