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
    "quantity": 10
}
doritos = {    
    "description": "Doritos",
    "barcode": "028400642262",
    "price_per_unit": 3.99,
    "quantity": 20
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

    # Add products
    product_resp1 = client.post(
        BASE_URL + "/products",
        headers=auth_header(auth_tokens, "admin"),
        json=chocolate_bar
    )
    assert product_resp1.status_code == 201
    product_barcode1 = product_resp1.json()["barcode"]

    # Create sale
    sale_resp = client.post(
        BASE_URL + "/sales",
        headers=auth_header(auth_tokens, "admin")
    )
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]

    # Add products to sale
    add_prod_resp = client.post(
        BASE_URL + f"/sales/{sale_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={ "barcode": product_barcode1, "amount": 3 }
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
        params={ "cash_amount": 20}
    )    
    assert pay_sale_resp.status_code == 200

    #Create return
    ret_creation_resp = client.post(
        BASE_URL + "/returns",
        params={"sale_id": sale_id},
        headers=auth_header(auth_tokens, "admin")
    )

    # Assert response
    assert ret_creation_resp.status_code == 201
    ret_id = ret_creation_resp.json()["id"]

    # Add item to return
    resp = client.post(
        BASE_URL + f"/returns/{ret_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": chocolate_bar["barcode"], "amount":1},
    )

    # Assert response
    assert resp.status_code == 201

    # Get return
    resp = client.get(
        BASE_URL + f"/returns/{ret_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200
    return resp.json()

@pytest.fixture
def closed_return_creation(client, auth_tokens):

    # Reset balance
    balance_resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(auth_tokens, "admin")
    )
    assert balance_resp.status_code == 205

    # Add products
    product_resp1 = client.post(
        BASE_URL + "/products",
        headers=auth_header(auth_tokens, "admin"),
        json=chocolate_bar
    )
    assert product_resp1.status_code == 201
    product_barcode1 = product_resp1.json()["barcode"]

    # Create sale
    sale_resp = client.post(
        BASE_URL + "/sales",
        headers=auth_header(auth_tokens, "admin")
    )
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]

    # Add products to sale
    add_prod_resp = client.post(
        BASE_URL + f"/sales/{sale_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={ "barcode": product_barcode1, "amount": 3 }
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
        params={ "cash_amount": 20}
    )    
    assert pay_sale_resp.status_code == 200

    #Create return
    ret_creation_resp = client.post(
        BASE_URL + "/returns",
        params={"sale_id": sale_id},
        headers=auth_header(auth_tokens, "admin")
    )

    # Assert response
    assert ret_creation_resp.status_code == 201
    ret_id = ret_creation_resp.json()["id"]

    # Add item to return
    resp = client.post(
        BASE_URL + f"/returns/{ret_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={"barcode": chocolate_bar["barcode"], "amount":1},
    )

    # Assert response
    assert resp.status_code == 201

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{ret_id}/close",
        headers=auth_header(auth_tokens, "admin")
    )

    assert close_resp.status_code == 200
    # Get return
    resp = client.get(
        BASE_URL + f"/returns/{ret_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200
    return resp.json()


# ---------------------------
# CLOSE RETURN TESTS 
# ---------------------------

def test_close_return_invalid_id(client, auth_tokens):

    for role in ["admin", "manager", "cashier"]:
        #Close return
        close_resp = client.patch(
            BASE_URL + f"/returns/-2/close",
            headers=auth_header(auth_tokens, role)
        )

        # Assert response
        assert close_resp.status_code == 400

def test_close_return_unauthenticated(client, auth_tokens,return_creation):
    return_id = return_creation["id"]

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "unauthorized")
    )
    # Assert response
    assert close_resp.status_code == 401
    
def test_close_return_not_found(client, auth_tokens):
    for role in ["admin", "manager", "cashier"]:
        #Close return
        close_resp = client.patch(
            BASE_URL + f"/returns/111/close",
            headers=auth_header(auth_tokens, role)
        )        
        # Assert response
        assert close_resp.status_code == 404

def test_close_return_invalid_state(client, auth_tokens, closed_return_creation):
    return_id = closed_return_creation["id"]

    for role in ["admin", "manager", "cashier"]:
        #Close return
        close_resp = client.patch(
            BASE_URL + f"/returns/{return_id}/close",
            headers=auth_header(auth_tokens, role)
        )
        # Assert response
        assert close_resp.status_code == 420



def test_close_return_success_admin(client, auth_tokens,return_creation):
    return_id = return_creation["id"]

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "admin")
    )

    assert close_resp.status_code == 200
    assert close_resp.json()["success"] == True
    # Get return
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"

def test_close_return_success_manager(client, auth_tokens,return_creation):
    return_id = return_creation["id"]

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "manager")
    )

    assert close_resp.status_code == 200
    assert close_resp.json()["success"] == True
    # Get return
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, "manager")
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"

def test_close_return_success_cashier(client, auth_tokens,return_creation):
    return_id = return_creation["id"]

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "cashier")
    )

    assert close_resp.status_code == 200
    assert close_resp.json()["success"] == True

    # Get return
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"