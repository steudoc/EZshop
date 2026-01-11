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
    "description": "Disposable Product",
    "barcode": "4006381333931", 
    "price_per_unit": 5.0,
    "quantity": 100,
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
    """Creates a simple product and returns its ID."""
    resp = client.post(
        BASE_URL + "/products", 
        json=product_sample, 
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    return resp.json()["id"]

@pytest.fixture
def product_in_transaction(client, auth_tokens, seeded_product):
    """
    Creates a product and adds it to an OPEN Sale.
    This product should be 'locked' from deletion.
    """
    product_id = seeded_product
    barcode = product_sample["barcode"]
    headers = auth_header(auth_tokens, "admin")

    # 1. Create Sale
    sale_resp = client.post(BASE_URL + "/sales", headers=headers)
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]

    # 2. Add Item to Sale
    client.post(
        BASE_URL + f"/sales/{sale_id}/items",
        headers=headers,
        params={"barcode": barcode, "amount": 1}
    )
    return product_id

# ----------------------------------------------------------------
# DELETE PRODUCT TESTS
# ----------------------------------------------------------------

def test_delete_product_success(client, auth_tokens, seeded_product):
    """
    Test that Administrator (or ShopManager) can delete an unused product.
    Expects 204 No Content.
    """
    product_id = seeded_product
    role = "admin"

    # 1. DELETE
    resp = client.delete(
        BASE_URL + f"/products/{product_id}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assert 204 No Content (Response body is empty)
    assert resp.status_code == 204
    assert resp.content == b""

    # 2. VERIFY (Should now be 404)
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert get_resp.status_code == 404


def test_delete_product_forbidden_cashier(client, auth_tokens, seeded_product):
    """
    Test that a Cashier cannot delete a product.
    Expects 403 Forbidden.
    """
    resp = client.delete(
        BASE_URL + f"/products/{seeded_product}",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 403
    


def test_delete_product_not_found(client, auth_tokens):
    """
    Test deleting a non-existent ID.
    Expects 404 Not Found.
    """
    resp = client.delete(
        BASE_URL + "/products/99999",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 404
    


def test_delete_product_invalid_id(client, auth_tokens):
    """
    Test deleting with invalid ID (<= 0).
    Expects 400 Bad Request.
    """
    invalid_ids = [0, -1]
    
    for pid in invalid_ids:
        resp = client.delete(
            BASE_URL + f"/products/{pid}",
            headers=auth_header(auth_tokens, "admin")
        )
        assert resp.status_code == 400
        


def test_delete_product_invalid_state_transaction_exists(client, auth_tokens, product_in_transaction):
    """
    Test 420 InvalidStateError:
    Cannot delete a product if it is part of a transaction (Sale/Order/Return).
    """
    product_id = product_in_transaction
    
    resp = client.delete(
        BASE_URL + f"/products/{product_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 420
    assert resp.json()["name"] == "InvalidStateError"
    # Ensure the product still exists
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert get_resp.status_code == 200


def test_delete_product_unauthenticated(client, auth_tokens, seeded_product):
    """
    Test that unauthenticated requests return 401 Unauthorized.
    """
    resp = client.delete(
        BASE_URL + f"/products/{seeded_product}",
        headers=auth_header(auth_tokens, "unauthorized")
    )
    
    assert resp.status_code == 401