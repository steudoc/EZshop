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
    "barcode": "4006381333931", # Valid GTIN-13
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
def seeded_product(client, auth_tokens):
    """Creates a valid product in the DB."""
    resp = client.post(
        BASE_URL + "/products", 
        json=product_sample, 
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    return resp.json()

# ----------------------------------------------------------------
# GET PRODUCT BY BARCODE TESTS
# ----------------------------------------------------------------

def test_get_by_barcode_success(client, auth_tokens, seeded_product):
    """
    Test that Administrator and ShopManager can retrieve a product by barcode.
    Expects 200 OK.
    """
    valid_barcode = seeded_product["barcode"]
    allowed_roles = ["admin", "manager"]

    for role in allowed_roles:
        resp = client.get(
            BASE_URL + f"/products/barcode/{valid_barcode}",
            headers=auth_header(auth_tokens, role)
        )
        
        # Assertions
        assert resp.status_code == 200, f"Role {role} failed"
        data = resp.json()
        assert data["barcode"] == valid_barcode
        assert data["description"] == product_sample["description"]


def test_get_by_barcode_forbidden_cashier(client, auth_tokens, seeded_product):
    """
    Test that a Cashier CANNOT access this endpoint.
    Expects 403 Forbidden.
    """
    valid_barcode = seeded_product["barcode"]
    
    resp = client.get(
        BASE_URL + f"/products/barcode/{valid_barcode}",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 403
    


def test_get_by_barcode_not_found(client, auth_tokens):
    """
    Test requesting a VALID barcode that does not exist in the DB.
    Expects 404 Not Found.
    """
    # 1234567890128 is a mathematically VALID GTIN-13 (Checksum 8 is correct for prefix 123456789012)
    # It must be valid, otherwise the API returns 400 before checking DB.
    valid_but_missing_barcode = "1234567890128"
    
    resp = client.get(
        BASE_URL + f"/products/barcode/{valid_but_missing_barcode}",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 404
   


@pytest.mark.parametrize("invalid_barcode, description", [
    ("123", "Too short"),
    ("123456789012345", "Too long"),
    ("abc1234567890", "Non-numeric"),
    ("4006381333932", "Invalid Checksum (Last digit modified)")
])
def test_get_by_barcode_bad_request(client, auth_tokens, invalid_barcode, description):
    """
    Test requesting invalid barcodes (Format or Checksum).
    Expects 400 Bad Request.
    """
    resp = client.get(
        BASE_URL + f"/products/barcode/{invalid_barcode}",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 400, f"Failed check for {description}"
    


def test_get_by_barcode_unauthenticated(client, auth_tokens, seeded_product):
    """
    Test requesting without a token.
    Expects 401 Unauthorized.
    """
    valid_barcode = seeded_product["barcode"]
    
    resp = client.get(
        BASE_URL + f"/products/barcode/{valid_barcode}",
        headers=auth_header(auth_tokens, "unauthorized")
    )
    
    assert resp.status_code == 401
   
def test_get_by_barcode_missing_barcode_param(client, auth_tokens):
    """
    Test requesting without providing a barcode.
    Expects 404 Not Found (since route won't match).
    """
    resp = client.get(
        BASE_URL + f"/products/barcode/",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 422   