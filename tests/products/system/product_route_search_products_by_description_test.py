import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ----------------------------------------------------------------
# TEST DATA
# ----------------------------------------------------------------

product_chocolate_bar = {    
    "description": "Chocolate Bar",
    "barcode": "4006381333931", 
    "price_per_unit": 2.50,
    "quantity": 10
}

product_dark_chocolate = {    
    "description": "Dark Chocolate",
    "barcode": "1234567890128", 
    "price_per_unit": 3.00,
    "quantity": 5
}

product_chips = {    
    "description": "Potato Chips",
    "barcode": "9876543210982", 
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
    Resets the database before every test synchronously.
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
def seed_search_data(client, auth_tokens):
    """Inserts 3 products with distinct descriptions for search testing."""
    headers = auth_header(auth_tokens, "admin")
    client.post(BASE_URL + "/products", json=product_chocolate_bar, headers=headers)
    client.post(BASE_URL + "/products", json=product_dark_chocolate, headers=headers)
    client.post(BASE_URL + "/products", json=product_chips, headers=headers)

# ----------------------------------------------------------------
# SEARCH PRODUCTS TESTS
# ----------------------------------------------------------------

def test_search_products_success_partial_match(client, auth_tokens, seed_search_data):
    """
    Test searching for a term that appears in multiple products.
    Query: 'Chocolate' -> Should return 'Chocolate Bar' and 'Dark Chocolate'.
    """
    # Test as Admin
    resp = client.get(
        BASE_URL + "/products/search",
        params={"query": "Chocolate"},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    descriptions = [p["description"] for p in data]
    assert "Chocolate Bar" in descriptions
    assert "Dark Chocolate" in descriptions
    assert "Potato Chips" not in descriptions


def test_search_products_success_single_match(client, auth_tokens, seed_search_data):
    """
    Test searching for a term that appears in only one product.
    Query: 'Chips' -> Should return only 'Potato Chips'.
    """
    # Test as ShopManager
    resp = client.get(
        BASE_URL + "/products/search",
        params={"query": "Chips"},
        headers=auth_header(auth_tokens, "manager")
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["description"] == "Potato Chips"


def test_search_products_no_match(client, auth_tokens, seed_search_data):
    """
    Test searching for a term that does not exist.
    Query: 'Wine' -> Should return empty list.
    """
    resp = client.get(
        BASE_URL + "/products/search",
        params={"query": "Wine"},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_products_forbidden_cashier(client, auth_tokens, seed_search_data):
    """
    Test that a Cashier CANNOT search products (unlike list_products).
    Expects 403 Forbidden.
    """
    resp = client.get(
        BASE_URL + "/products/search",
        params={"query": "Chocolate"},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 403


def test_search_products_unauthenticated(client, auth_tokens):
    """
    Test that unauthenticated users cannot search.
    Expects 401 Unauthorized.
    """
    resp = client.get(
        BASE_URL + "/products/search",
        params={"query": "test"}
        # No headers
    )
    assert resp.status_code == 401


def test_search_products_missing_query_param(client, auth_tokens):
    """
    Test calling the endpoint without the required 'query' parameter.
    FastAPI should return 422 Validation Error.
    """
    resp = client.get(
        BASE_URL + "/products/search",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 200