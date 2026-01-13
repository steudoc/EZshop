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
def auth_tokens(client):
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

    product_resp2 = client.post(
        BASE_URL + "/products",
        headers=auth_header(auth_tokens, "admin"),
        json=doritos
    )
    

    assert product_resp2.status_code == 201
    product_barcode2 = product_resp2.json()["barcode"]

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

    # Add products to sale
    add_prod_resp = client.post(
        BASE_URL + f"/sales/{sale_id}/items",
        headers=auth_header(auth_tokens, "admin"),
        params={ "barcode": product_barcode2, "amount": 2 }
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

    # Add products to return transaction
    add_resp = client.post(
        BASE_URL + f"/returns/{ret_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":2},
        headers=auth_header(auth_tokens, "admin")
    )  

    # Assert response
    assert add_resp.status_code == 201  


    return ret_creation_resp.json()

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
    # Assert response
    assert close_resp.status_code == 200

    # Get return
    resp = client.get(
        BASE_URL + f"/returns/{ret_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200
    return resp.json()



# ---------------------------
# REMOVE ITEM TESTS 
# ---------------------------

def test_remove_item_unauthenticated(client, auth_tokens,returns_creation):
    return_id = returns_creation["id"]
    # Remove item to return
    resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        headers=auth_header(auth_tokens, "unauthorized"),
        params={"barcode": chocolate_bar["barcode"], "amount":1},
    )

    # Assert response
    assert resp.status_code == 401

def test_remove_item_not_found(client, auth_tokens,returns_creation):
    return_id = returns_creation["id"]

    for role in ["admin", "manager", "cashier"]:
        # Remote item to return
        resp = client.delete(
            BASE_URL + f"/returns/{return_id}/items",
            headers=auth_header(auth_tokens, role),
            params={"barcode": "038000844980", "amount":1},
        )

        # Assert response
        assert resp.status_code == 404

def test_remove_item_invalid_or_missing_param(client, auth_tokens):

    for role in ["admin", "manager", "cashier"]:
        # Remove item to return
        resp = client.delete(
            BASE_URL + "/returns/-2020/items",
            headers=auth_header(auth_tokens, role),
            params={"barcode": chocolate_bar["barcode"], "amount":1},
        )
        # Assert response
        assert resp.status_code == 400

        # Remove item to return
        resp = client.delete(
            BASE_URL + "/returns/-2020/items",
            headers=auth_header(auth_tokens, role),
            params={"barcode": chocolate_bar["barcode"], "amount":-1},
        )
        # Assert response
        assert resp.status_code == 400
        

def test_remove_item_to_closed_return(client, auth_tokens,closed_return_creation):
    return_id = closed_return_creation["id"]

    for role in ["admin", "manager", "cashier"]:
        # Remove item to return
        resp = client.delete(
            BASE_URL + f"/returns/{return_id}/items",
            headers=auth_header(auth_tokens, role),
            params={"barcode": chocolate_bar["barcode"], "amount":1},
        )

        # Assert response
        assert resp.status_code == 420

def test_remove_more_items_compared_to_sale(client, auth_tokens,returns_creation):
    return_id = returns_creation["id"]

    for role in ["admin", "manager", "cashier"]:
        # Try to remove an item that was never added to the return
        rem_resp = client.delete(
            BASE_URL + f"/returns/{return_id}/items",
            params={"barcode": doritos["barcode"], "amount":30},
            headers=auth_header(auth_tokens, role)
        )

        # Item not found in return
        assert rem_resp.status_code == 404


def test_remove_item_success_admin(client, auth_tokens,returns_creation):
    return_id = returns_creation["id"]

    role = "admin"
    
    # Get the current return to see what items it has
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    # The fixture already added 2 chocolate_bar items to this return
    assert len(resp.json()["lines"]) == 1
    initial_quantity = resp.json()["lines"][0]["quantity"]
    assert initial_quantity == 2

    # Remove one item from return transaction
    rem_resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, role)
    )  

    # Assert response (202 Accepted for successful DELETE)
    assert rem_resp.status_code == 202

    # Get return and verify item quantity decreased
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert len(resp.json()["lines"]) == 1
    assert resp.json()["lines"][0]["quantity"] == 1

    # Remove the last item from return transaction
    rem_resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, role)
    )  

    # Assert response
    assert rem_resp.status_code == 202

    # Get return and verify line was deleted
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert len(resp.json()["lines"]) == 0

def test_remove_item_success_manager(client, auth_tokens,returns_creation):
    return_id = returns_creation["id"]

    role = "manager"
    
    # Get the current return to see what items it has
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    # The fixture already added 2 chocolate_bar items to this return
    assert len(resp.json()["lines"]) == 1
    initial_quantity = resp.json()["lines"][0]["quantity"]
    assert initial_quantity == 2

    # Remove one item from return transaction
    rem_resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, role)
    )  

    # Assert response (202 Accepted for successful DELETE)
    assert rem_resp.status_code == 202

    # Get return and verify item quantity decreased
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert len(resp.json()["lines"]) == 1
    assert resp.json()["lines"][0]["quantity"] == 1

    # Remove the last item from return transaction
    rem_resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, role)
    )  

    # Assert response
    assert rem_resp.status_code == 202

    # Get return and verify line was deleted
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert len(resp.json()["lines"]) == 0

def test_remove_item_success_cashier(client, auth_tokens,returns_creation):
    return_id = returns_creation["id"]

    role = "cashier"
    
    # Get the current return to see what items it has
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    # The fixture already added 2 chocolate_bar items to this return
    assert len(resp.json()["lines"]) == 1
    initial_quantity = resp.json()["lines"][0]["quantity"]
    assert initial_quantity == 2

    # Remove one item from return transaction
    rem_resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, role)
    )  

    # Assert response (202 Accepted for successful DELETE)
    assert rem_resp.status_code == 202

    # Get return and verify item quantity decreased
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert len(resp.json()["lines"]) == 1
    assert resp.json()["lines"][0]["quantity"] == 1

    # Remove the last item from return transaction
    rem_resp = client.delete(
        BASE_URL + f"/returns/{return_id}/items",
        params={"barcode": chocolate_bar["barcode"], "amount":1},
        headers=auth_header(auth_tokens, role)
    )  

    # Assert response
    assert rem_resp.status_code == 202

    # Get return and verify line was deleted
    resp = client.get(
        BASE_URL + f"/returns/{return_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert len(resp.json()["lines"]) == 0