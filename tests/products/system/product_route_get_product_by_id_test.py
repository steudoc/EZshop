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
    "description": "Milka Chocolate",
    "barcode": "4006381333931", # Valid GTIN-13 with correct checksum
    "price_per_unit": 2.50,
    "quantity": 10,
    "position": "1-A-10" 
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
    """
    Resets the database synchronously before every test.
    """
    async def _reset_action():
        await reset()
        await init_db()
    
    asyncio.run(_reset_action())

@pytest.fixture(scope="function")
def auth_tokens(client, setup_database):
    """Authenticate users once and return their JWT tokens."""
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
def seeded_product_id(client, auth_tokens):
    """
    Creates a valid product and returns its ID.
    """
    resp = client.post(
        BASE_URL + "/products", 
        json=product_sample, 
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    return resp.json()["id"]

# ----------------------------------------------------------------
# GET PRODUCT BY ID TESTS
# ----------------------------------------------------------------

def test_get_product_by_id_success(client, auth_tokens, seeded_product_id):
    """
    Test that Administrator, ShopManager, and Cashier can retrieve a product by ID.
    Expects 200 OK.
    """
    allowed_roles = ["admin", "manager", "cashier"]
    product_id = seeded_product_id

    for role in allowed_roles:
        resp = client.get(
            BASE_URL + f"/products/{product_id}",
            headers=auth_header(auth_tokens, role)
        )
        
        # Assertions
        assert resp.status_code == 200, f"Role {role} failed to get product"
        data = resp.json()
        assert data["id"] == product_id
        assert data["barcode"] == product_sample["barcode"]
        assert data["description"] == product_sample["description"]


def test_get_product_by_id_not_found(client, auth_tokens):
    """
    Test requesting a non-existent ID.
    Expects 404 Not Found.
    """
    non_existent_id = 99999
    
    resp = client.get(
        BASE_URL + f"/products/{non_existent_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 404
    


def test_get_product_by_id_bad_request_invalid_id(client, auth_tokens):
    """
    Test requesting an invalid ID (<= 0).
    Expects 400 Bad Request.
    """
    invalid_ids = [0, -1, -100]
    
    for pid in invalid_ids:
        resp = client.get(
            BASE_URL + f"/products/{pid}",
            headers=auth_header(auth_tokens, "admin")
        )
        
        assert resp.status_code == 400
        


def test_get_product_by_id_unauthenticated(client, auth_tokens, seeded_product_id):
    """
    Test requesting without a token.
    Expects 401 Unauthorized.
    """
    resp = client.get(
        BASE_URL + f"/products/{seeded_product_id}",
        headers=auth_header(auth_tokens, "unauthorized")
    )
    
    assert resp.status_code == 401

