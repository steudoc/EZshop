import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ----------------------------------------------------------------
# TEST DATA
# ----------------------------------------------------------------

# Using valid GTINs/Barcodes to ensure creation succeeds
product_1 = {    
    "description": "Chocolate Bar",
    "barcode": "4006381333931", # Valid GTIN-13
    "price_per_unit": 2.50,
    "quantity": 10,
    "position": "1-A-10" 
}

product_2 = {    
    "description": "Chips",
    "barcode": "012345678905",  # Valid GTIN-12/UPC
    "price_per_unit": 1.50,
    "quantity": 20
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
    Resets the database before every test.
    Uses asyncio.run() to execute async code synchronously, 
    preventing conflicts with TestClient and pytest-asyncio.
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
def seed_products(client, auth_tokens):
    """Helper fixture to insert products into the DB before listing tests."""
    client.post(BASE_URL + "/products", json=product_1, headers=auth_header(auth_tokens, "admin"))
    client.post(BASE_URL + "/products", json=product_2, headers=auth_header(auth_tokens, "admin"))

# ----------------------------------------------------------------
# LIST PRODUCTS TESTS
# ----------------------------------------------------------------

def test_list_products_empty(client, auth_tokens):
    """
    Test that the endpoint returns an empty list (200 OK) 
    when no products exist in the database.
    """
    resp = client.get(
        BASE_URL + "/products",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_products_success_all_roles(client, auth_tokens, seed_products):
    """
    Test that Administrator, ShopManager, and Cashier 
    can successfully retrieve the list of products.
    """
    allowed_roles = ["admin", "manager", "cashier"]

    for role in allowed_roles:
        resp = client.get(
            BASE_URL + "/products",
            headers=auth_header(auth_tokens, role)
        )
        
        # Assert Status
        assert resp.status_code == 200
        
        # Assert Data
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify content (check if barcodes are present)
        barcodes = [p["barcode"] for p in data]
        assert product_1["barcode"] in barcodes
        assert product_2["barcode"] in barcodes


def test_list_products_unauthenticated(client, auth_tokens):
    """
    Test that an unauthenticated request returns 401 Unauthorized.
    """
    # Case 1: Wrong/Empty token
    resp = client.get(
        BASE_URL + "/products",
        headers=auth_header(auth_tokens, "unauthorized")
    )
    assert resp.status_code == 401
    
    # Case 2: No Authorization header
    resp_no_header = client.get(BASE_URL + "/products")
    assert resp_no_header.status_code == 401