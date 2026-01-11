import asyncio
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db
from datetime import datetime, timedelta


BASE_URL = "http://127.0.0.1:8000/api/v1"


valid_product = {    
    "description": "New Product",
    "barcode": "4006381333931", 
    "price_per_unit": 10.50,
    "note": "Test note",
    "quantity": 10,
    "position": "1-A-10" 
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

# ---------------------------
# CREATE PRODUCT TESTS 
# ---------------------------

def test_create_product_success_valid_gtin_and_position(client, auth_tokens):
    """
    Test success with strictly valid GTINs and Position format.
    """
    # 1. Test Admin with GTIN-13
    product_admin = valid_product.copy()
    product_admin["barcode"] = "4006381333931" # Valid GTIN-13
    product_admin["position"] = "100-B-20"     # Valid Position
    
    resp = client.post(
        BASE_URL + "/products",
        json=product_admin,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    assert resp.json()["barcode"] == product_admin["barcode"]

    # 2. Test Manager with GTIN-12 (UPC valid checksum)
    # 012345678905 -> Valid UPC/GTIN-12
    product_manager = valid_product.copy()
    product_manager["barcode"] = "012345678905" 
    product_manager["position"] = "" # Empty position is allowed by is_position_valid
    
    resp = client.post(
        BASE_URL + "/products",
        json=product_manager,
        headers=auth_header(auth_tokens, "manager")
    )
    assert resp.status_code == 201


def test_create_product_insufficient_permissions(client, auth_tokens):
    """Cashier cannot create products."""
    resp = client.post(
        BASE_URL + "/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


def test_create_product_insufficient_permissions(client, auth_tokens):
    """Unauthorized user cannot create products."""
    resp = client.post(
        BASE_URL + "/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "unauthorized")
    )
    assert resp.status_code == 401


@pytest.mark.parametrize("field, invalid_value, description", [
    # --- BARCODE FORMAT (Structural) ---
    ("barcode", "12345678901", "Too short"),
    ("barcode", "123456789012345", "Too long"),
    ("barcode", "400638133393A", "Non-numeric"),
    ("barcode", "", "Empty string"),
    ("barcode", None, "None value"),

    # --- BARCODE CHECKSUM (Logical) ---
    ("barcode", "4006381333932", "Invalid Checksum"),

    # --- POSITION FORMAT ---
    ("position", "Shelf1", "No separators"),
    ("position", "1-2", "Missing middle part"),
    ("position", "A-1-B", "Wrong order"),
    ("position", "1-@-2", "Special chars"),
    ("position", "1-A-", "Missing suffix"),

    # --- PRICE ERRORS ---
    ("price_per_unit", -1.5, "Negative price"),
    ("price_per_unit", None, "None price"),

    # --- QUANTITY ERRORS ---
    ("quantity", -1, "Negative quantity"),

    # --- DESCRIPTION ERRORS ---
    ("description", "", "Empty description"),
    ("description", None, "None description"),
])
def test_create_product_invalid_input(client, auth_tokens, field, invalid_value, description):
    """
    Test parametrizzato che verifica tutti i casi di input invalido (400 Bad Request).
    Sostituisce le funzioni separate unificando la logica.
    """
    # 1. Copia il prodotto valido
    payload = valid_product.copy()

    # 2. Inserisce il valore invalido nel campo specifico
    payload[field] = invalid_value

    # 3. Esegue la richiesta
    resp = client.post(
        BASE_URL + "/products",
        json=payload,
        headers=auth_header(auth_tokens, "admin")
    )

    # 4. Asserzione
    assert resp.status_code == 400, f"Failed check for {field}: {description}"


def test_create_product_conflict_duplicate_barcode(client, auth_tokens):
    """
    Returns 409 if provided barcode is already used.
    """
    # 1. Create first product
    resp1 = client.post(
        BASE_URL + "/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp1.status_code == 201

    # 2. Try to create same product again
    resp2 = client.post(
        BASE_URL + "/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp2.status_code == 409
    assert resp2.json()["name"] == "ConflictError"