import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ----------------------------------------------------------------
# TEST DATA
# ----------------------------------------------------------------

product_sample_1 = {    
    "description": "Product A",
    "barcode": "4006381333931", 
    "price_per_unit": 10.0,
    "quantity": 5,
    "position": None # Initially without a position
}

product_sample_2 = {    
    "description": "Product B",
    "barcode": "1234567890128", 
    "price_per_unit": 5.0,
    "quantity": 10,
    "position": "100-A-10" # Already positioned
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
def seeded_products(client, auth_tokens):
    """Creates two products: one without position, one with position."""
    headers = auth_header(auth_tokens, "admin")
    
    # Create Product 1 (ID likely 1)
    resp1 = client.post(BASE_URL + "/products", json=product_sample_1, headers=headers)
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    # Create Product 2 (ID likely 2)
    resp2 = client.post(BASE_URL + "/products", json=product_sample_2, headers=headers)
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]
    
    return {"p1_id": id1, "p2_id": id2}

# ----------------------------------------------------------------
# ASSIGN POSITION TESTS
# ----------------------------------------------------------------

def test_assign_position_lifecycle(client, auth_tokens, seeded_products):
    """
    Test the complete position lifecycle:
    1. Assign a new valid position (Success).
    2. Verify update via GET.
    3. Clear the position (send empty string).
    4. Verify the position is cleared.
    """
    product_id = seeded_products["p1_id"] # Product A (initial position: None)
    new_position = "2-B-20"
    role = "admin"

    # 1. ASSIGN NEW POSITION
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/position",
        params={"position": new_position},
        headers=auth_header(auth_tokens, role)
    )
    assert resp.status_code == 201 
    assert resp.json()["success"] is True

    # 2. VERIFY UPDATE
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}", 
        headers=auth_header(auth_tokens, role)
    )
    assert get_resp.json()["position"] == new_position

    # 3. CLEAR POSITION (Send empty string)
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/position",
        params={"position": ""},
        headers=auth_header(auth_tokens, role)
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True

    # 4. VERIFY CLEARED
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}", 
        headers=auth_header(auth_tokens, role)
    )
    # Position should be None or empty string depending on DB implementation
    assert get_resp.json()["position"] in [None, ""]


def test_assign_position_conflict(client, auth_tokens, seeded_products):
    """
    Test ConflictError (409):
    Try to assign Product A to the position currently occupied by Product B.
    """
    product_a_id = seeded_products["p1_id"]
    # Product B is at "100-A-10"
    occupied_position = product_sample_2["position"] 
    
    resp = client.patch(
        BASE_URL + f"/products/{product_a_id}/position",
        params={"position": occupied_position},
        headers=auth_header(auth_tokens, "manager")
    )
    
    assert resp.status_code == 409
    


def test_assign_position_forbidden_cashier(client, auth_tokens, seeded_products):
    """
    Test that a Cashier cannot change a product's position.
    Expects 403 Forbidden.
    """
    product_id = seeded_products["p1_id"]
    
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 403
    


def test_assign_position_not_found(client, auth_tokens):
    """
    Test attempting to update a non-existent product ID.
    Expects 404 Not Found.
    """
    resp = client.patch(
        BASE_URL + "/products/99999/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 404
    


@pytest.mark.parametrize("invalid_position, reason", [
    ("Shelf-1", "No separators"),
    ("1-2", "Missing section"),
    ("A-1-A", "Wrong format order"),
    ("1-@-1", "Special characters"),
    (" ", "Whitespace string (not empty)"),
])
def test_assign_position_invalid_format(client, auth_tokens, seeded_products, invalid_position, reason):
    """
    Test 400 Bad Request for invalid position string formats.
    """
    product_id = seeded_products["p1_id"]
    
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/position",
        params={"position": invalid_position},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code == 400, f"Failed check for {reason}"
    


def test_assign_position_invalid_id(client, auth_tokens):
    """
    Test 400 Bad Request for invalid IDs (<= 0).
    """
    resp = client.patch(
        BASE_URL + "/products/0/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 400
    


def test_assign_position_unauthenticated(client, auth_tokens, seeded_products):
    """
    Test that unauthenticated requests return 401 Unauthorized.
    """
    product_id = seeded_products["p1_id"]
    
    resp = client.patch(
        BASE_URL + f"/products/{product_id}/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "unauthorized")
    )
    
    assert resp.status_code == 401