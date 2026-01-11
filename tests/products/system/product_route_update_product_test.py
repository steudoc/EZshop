import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ----------------------------------------------------------------
# TEST DATA
# ----------------------------------------------------------------

# Valid Product A
product_data_a = {    
    "description": "Original Product",
    "barcode": "4006381333931", # Valid GTIN-13 (Checksum 1)
    "price_per_unit": 10.0,
    "quantity": 10,
    "position": "1-A-1"
}

# Valid Product B (For conflict testing)
product_data_b = {    
    "description": "Other Product",
    "barcode": "1234567890128", # Valid GTIN-13 (Checksum 8)
    "price_per_unit": 5.0,
    "quantity": 20,
    "position": "2-B-2"
}

# Update Data (Valid)
update_payload = {
    "description": "Updated Description",
    "barcode": "9876543210982", # New Valid GTIN-13 (Checksum 2)
    "price_per_unit": 15.50,
    "quantity": 50,
    "position": "3-C-3",
    "note": "Updated note"
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
    """Creates Product A and returns its ID."""
    resp = client.post(
        BASE_URL + "/products", 
        json=product_data_a, 
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    return resp.json()["id"]

@pytest.fixture
def seeded_product_with_sale(client, auth_tokens, seeded_product):
    """
    Creates a product, creates a sale, and adds the product to the sale.
    This puts the product in a state where barcode update should fail.
    """
    product_id = seeded_product
    barcode = product_data_a["barcode"]
    headers = auth_header(auth_tokens, "admin")

    # 1. Create Sale
    sale_resp = client.post(BASE_URL + "/sales", headers=headers)
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]

    # 2. Add Item to Sale
    item_resp = client.post(
        BASE_URL + f"/sales/{sale_id}/items",
        headers=headers,
        params={"barcode": barcode, "amount": 1}
    )
    assert item_resp.status_code == 201
    
    return product_id

# ----------------------------------------------------------------
# UPDATE PRODUCT TESTS
# ----------------------------------------------------------------

def test_update_product_success(client, auth_tokens, seeded_product):
    """
    Test successful update of all fields (Description, Price, Qty, Barcode, Position).
    Conditions: No sales associated.
    """
    product_id = seeded_product
    role = "admin"

    # Perform Update
    resp = client.put(
        BASE_URL + f"/products/{product_id}",
        json=update_payload,
        headers=auth_header(auth_tokens, role)
    )

    # Verify Response
    assert resp.status_code == 201
    assert resp.json()["success"] is True

    # Verify Data Persisted
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}",
        headers=auth_header(auth_tokens, role)
    )
    data = get_resp.json()
    assert data["description"] == update_payload["description"]
    assert data["price_per_unit"] == update_payload["price_per_unit"]
    assert data["barcode"] == update_payload["barcode"] # Barcode updated
    assert data["position"] == update_payload["position"]


def test_update_product_forbidden_cashier(client, auth_tokens, seeded_product):
    """Cashier cannot update products (403)."""
    resp = client.put(
        BASE_URL + f"/products/{seeded_product}",
        json=update_payload,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403
    


def test_update_product_not_found(client, auth_tokens):
    """Update non-existent ID (404)."""
    resp = client.put(
        BASE_URL + "/products/99999",
        json=update_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 404
    assert resp.json()["name"] == "NotFoundError"


# ----------------------------------------------------------------
# VALIDATION TESTS (400)
# ----------------------------------------------------------------

@pytest.mark.parametrize("field, invalid_value, description", [
    ("price_per_unit", -5.0, "Negative Price"),
    ("price_per_unit", 0, "Zero Price (if strictly >0 required)"), 
    ("quantity", -1, "Negative Quantity"),
    ("barcode", "123", "Barcode too short"),
    ("barcode", "4006381333932", "Invalid Checksum"),
    ("barcode", None, "Missing Barcode"),
])
def test_update_product_validation_error(client, auth_tokens, seeded_product, field, invalid_value, description):
    """Test 400 Bad Request for various invalid inputs."""
    
    # Start with valid update data
    payload = update_payload.copy()
    # Inject invalid value
    payload[field] = invalid_value

    resp = client.put(
        BASE_URL + f"/products/{seeded_product}",
        json=payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 400, f"Failed check for {description}"
    


def test_update_product_invalid_id(client, auth_tokens):
    """Update with invalid ID param <= 0 (400)."""
    resp = client.put(
        BASE_URL + "/products/0",
        json=update_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 400


# ----------------------------------------------------------------
# CONFLICT TESTS (409)
# ----------------------------------------------------------------

def test_update_product_conflict_barcode(client, auth_tokens, seeded_product):
    """
    Test 409 Conflict: Try to update Product A's barcode to match Product B's barcode.
    """
    headers = auth_header(auth_tokens, "admin")
    
    # 1. Create Product B
    client.post(BASE_URL + "/products", json=product_data_b, headers=headers)

    # 2. Try to update Product A to use Product B's barcode
    payload = update_payload.copy()
    payload["barcode"] = product_data_b["barcode"] # Conflict

    resp = client.put(
        BASE_URL + f"/products/{seeded_product}",
        json=payload,
        headers=headers
    )
    
    assert resp.status_code == 409
    


# ----------------------------------------------------------------
# LOGIC / STATE TESTS (420)
# ----------------------------------------------------------------

def test_update_barcode_fails_if_transaction_exists(client, auth_tokens, seeded_product_with_sale):
    """
    Test 420 InvalidStateError:
    Cannot update BARCODE if the product is associated with an open sale.
    """
    product_id = seeded_product_with_sale
    
    # Payload trying to change barcode
    payload = update_payload.copy()
    payload["barcode"] = "9876543210982" # Different valid barcode

    resp = client.put(
        BASE_URL + f"/products/{product_id}",
        json=payload,
        headers=auth_header(auth_tokens, "admin")
    )

    assert resp.status_code == 420
    


def test_update_other_fields_allowed_with_transaction(client, auth_tokens, seeded_product_with_sale):
    """
    Logic Check: Even if a transaction exists, we SHOULD be able to update 
    Description or Price, provided the Barcode remains the same.
    """
    product_id = seeded_product_with_sale
    
    # Payload keeps the ORIGINAL barcode, but changes description/price
    payload = update_payload.copy()
    payload["barcode"] = product_data_a["barcode"] # Same barcode as original
    payload["description"] = "New Desc Allowed"
    payload["price_per_unit"] = 20.0

    resp = client.put(
        BASE_URL + f"/products/{product_id}",
        json=payload,
        headers=auth_header(auth_tokens, "admin")
    )

    assert resp.status_code == 201
    assert resp.json()["success"] is True

    # Verify update
    get_resp = client.get(
        BASE_URL + f"/products/{product_id}", 
        headers=auth_header(auth_tokens, "admin")
    )
    assert get_resp.json()["description"] == "New Desc Allowed"