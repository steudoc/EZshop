import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ----------------------------------------------------------------
# TEST DATA
# ----------------------------------------------------------------

product_sample = {    
    "description": "Milk",
    "barcode": "4006381333931", 
    "price_per_unit": 1.50,
    "quantity": 10, # Initial quantity
    "position": "1-A-1" 
}

# ----------------------------------------------------------------
# FIXTURES
# ----------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Resets the database synchronously before every test."""
    async def _reset_action():
        await reset()
        await init_db()
    asyncio.run(_reset_action())

@pytest.fixture(scope="function")
def auth_tokens(client, setup_database):
    """Authenticate users."""
    users = {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }
    tokens = {}
    for role, creds in users.items():
        resp = client.post(BASE_URL + "/auth", json=creds)
        assert resp.status_code == 200
        tokens[role] = f"Bearer {resp.json()['token']}"
    tokens["unauthorized"] = ""
    return tokens

def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}

@pytest.fixture
def seeded_product(client, auth_tokens):
    """Creates a product with 10 units in stock."""
    resp = client.post(
        BASE_URL + "/products", 
        json=product_sample, 
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    return resp.json()

# ----------------------------------------------------------------
# UPDATE QUANTITY TESTS
# ----------------------------------------------------------------

def test_increment_quantity_success(client, auth_tokens, seeded_product):
    """
    Test increasing the quantity (Positive number).
    Start: 10, Add: 5 -> Result: 15.
    """
    product_id = seeded_product["id"]
    quantity_to_add = 5
    role = "admin"

    # 1. Perform Increment
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/quantity",
        params={"quantity": quantity_to_add},
        headers=auth_header(auth_tokens, role)
    )
    
    assert resp.status_code == 201
    assert resp.json()["success"] is True

    # 2. Verify Update
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}", 
        headers=auth_header(auth_tokens, role)
    )
    assert get_resp.json()["quantity"] == 15


def test_decrement_quantity_success(client, auth_tokens, seeded_product):
    """
    Test decreasing the quantity (Negative number).
    Start: 10, Remove: 3 -> Result: 7.
    """
    product_id = seeded_product["id"]
    quantity_to_remove = -3
    role = "manager"

    # 1. Perform Decrement
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/quantity",
        params={"quantity": quantity_to_remove},
        headers=auth_header(auth_tokens, role)
    )
    
    assert resp.status_code == 201
    assert resp.json()["success"] is True

    # 2. Verify Update
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}", 
        headers=auth_header(auth_tokens, role)
    )
    assert get_resp.json()["quantity"] == 7


def test_decrement_quantity_insufficient_stock(client, auth_tokens, seeded_product):
    """
    Test 400 Bad Request when trying to remove more than available.
    Start: 10, Remove: 20 -> Resulting quantity would be negative.
    """
    product_id = seeded_product["id"]
    quantity_to_remove = -20 # Too much
    
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/quantity",
        params={"quantity": quantity_to_remove},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 400
    


def test_quantity_forbidden_cashier(client, auth_tokens, seeded_product):
    """
    Test that a Cashier cannot modify quantity.
    Expects 403 Forbidden.
    """
    product_id = seeded_product["id"]
    
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/quantity",
        params={"quantity": 1},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 403
    


def test_quantity_not_found(client, auth_tokens):
    """
    Test attempting to update a non-existent product ID.
    Expects 404 Not Found.
    """
    resp = client.patch(
        BASE_URL + "/products/99999/quantity",
        params={"quantity": 10},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 404
    


def test_quantity_invalid_id(client, auth_tokens):
    """
    Test 400 Bad Request for invalid IDs (<= 0).
    """
    resp = client.patch(
        BASE_URL + "/products/0/quantity",
        params={"quantity": 5},
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 400



def test_quantity_unauthenticated(client, auth_tokens, seeded_product):
    """
    Test that unauthenticated requests return 401 Unauthorized.
    """
    product_id = seeded_product["id"]
    
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/quantity",
        params={"quantity": 5},
        headers=auth_header(auth_tokens, "unauthorized")
    )
    
    assert resp.status_code == 401