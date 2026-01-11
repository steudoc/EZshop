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
    "quantity": 200
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
def returns_creation(client, auth_tokens):

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
        params={ "barcode": product_barcode1, "amount": 2 }
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

    # Add product to return transaction
    add_resp = client.post(
        BASE_URL + f"/returns/{ret_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, "admin")
    )  

    # Assert response
    assert add_resp.status_code == 201  

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{ret_id}/close",
        headers=auth_header(auth_tokens, "admin")
    )
    # Assert response
    assert close_resp.status_code == 200


    return ret_id



@pytest.fixture
def return_reimbursed(client, auth_tokens):

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
        params={ "barcode": product_barcode1, "amount": 2 }
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

    # Add product to return transaction
    add_resp = client.post(
        BASE_URL + f"/returns/{ret_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, "admin")
    )  

    # Assert response
    assert add_resp.status_code == 201  

    #Close return
    close_resp = client.patch(
        BASE_URL + f"/returns/{ret_id}/close",
        headers=auth_header(auth_tokens, "admin")
    )
    # Assert response
    assert close_resp.status_code == 200

    #Reimburse return
    reim_resp = client.patch(
        BASE_URL + f"/returns/{ret_id}/reimburse",
        headers=auth_header(auth_tokens, "admin")
    )
    # Assert response
    assert reim_resp.status_code == 200


    return ret_id

# ---------------------------
# DELETE TRANSACTION TESTS 
# ---------------------------

def test_delete_return_success_authorized_admin(client, auth_tokens,returns_creation):
        # Delete return
        resp = client.delete(
            BASE_URL + f"/returns/{returns_creation}",
            headers=auth_header(auth_tokens, "admin")
        )
        # Assert response
        assert resp.status_code == 204

def test_delete_return_success_authorized_manager(client, auth_tokens,returns_creation):
        # Delete return
        resp = client.delete(
            BASE_URL + f"/returns/{returns_creation}",
            headers=auth_header(auth_tokens, "manager")
        )
        # Assert response
        assert resp.status_code == 204

def test_delete_return_success_authorized_cashier(client, auth_tokens,returns_creation):
        # Delete return
        resp = client.delete(
            BASE_URL + f"/returns/{returns_creation}",
            headers=auth_header(auth_tokens, "cashier")
        )
        # Assert response
        assert resp.status_code == 204
    

def test_delete_return_unauthenticated(client, auth_tokens,returns_creation):
    # Delete return
    resp = client.delete(
        BASE_URL + f"/returns/{returns_creation}",
        headers=auth_header(auth_tokens, "unauthorized")
    )

    # Assert response
    assert resp.status_code == 401


def test_delete_return_invalid_or_missing_id_admin(client, auth_tokens):
        # Delete return
        resp = client.delete(
            BASE_URL + "/returns/-2",
            headers=auth_header(auth_tokens, "admin")
        )

        # Assert response
        assert resp.status_code == 400



def test_delete_return_not_found(client, auth_tokens):
    for role in ["admin", "manager", "cashier"]:
        # Get return
        resp = client.delete(
            BASE_URL + "/returns/3444",
            headers=auth_header(auth_tokens, role)
        )

        # Assert response
        assert resp.status_code == 404


def test_delete_reimbursed_return(client, auth_tokens, return_reimbursed):
     for role in ["admin", "manager", "cashier"]:
        # Get return
        resp = client.delete(
            BASE_URL + f"/returns/{return_reimbursed}",
            headers=auth_header(auth_tokens, role)
        )

        # Assert response
        assert resp.status_code == 420