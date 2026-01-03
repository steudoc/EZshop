# tests/orders/integration/test_order_integration.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db
from datetime import datetime

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


BASE_URL = "http://127.0.0.1:8000/api/v1"


# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

# First create a product to use in orders
PRODUCT_SAMPLE = {
    "barcode": "5901234123457",
    "description": "Test Product",
    "price_per_unit": 29.99,
    "quantity": 100,
    "position": "1-A-1"
}

ORDER_ISSUED_SAMPLE = {
    "product_barcode": "5901234123457",
    "quantity": 5,
    "price_per_unit": 29.99,
    "status": "ISSUED",
    "issue_date": None
}

ORDER_PAID_SAMPLE = {
    "product_barcode": "5901234123457",
    "quantity": 3,
    "price_per_unit": 29.99,
    "status": "PAID",
    "issue_date": None
}


# ---------------------------
# GLOBAL FIXTURE FOR TOKENS AND SETUP
# ---------------------------

@pytest.fixture(scope="session", autouse=True)
def auth_tokens(event_loop, client):
    """Authenticate users once and return their JWT tokens."""

    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
    
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
    
    # Initialize system balance via HTTP endpoint
    balance_resp = client.post(BASE_URL + "/balance/set?amount=10000", headers=auth_header(tokens, "admin"))
    print(f"\nBalance initialization status: {balance_resp.status_code}")
    assert balance_resp.status_code == 201, f"Failed to set balance: {balance_resp.text}"
    
    # Create product after getting tokens
    print(f">>> Creating product with data: {PRODUCT_SAMPLE}")
    product_resp = client.post(BASE_URL + "/products", json=PRODUCT_SAMPLE, headers=auth_header(tokens, "admin"))
    print(f">>> Product creation status: {product_resp.status_code}")
    print(f">>> Product response: {product_resp.text}")
    assert product_resp.status_code == 201, f"Failed to create product: {product_resp.text}"

    return tokens


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}


# ---------------------------
# SETUP: CREATE PRODUCT BEFORE ORDERS
# ---------------------------
# Product is created in auth_tokens fixture during setup

# ---------------------------
# CREATE ORDER TESTS
# ---------------------------

def test_create_issued_order_success(client, auth_tokens):
    """Test creating an issued order"""
    print(f"\n>>> Creating order with data: {ORDER_ISSUED_SAMPLE}")
    resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    print(f">>> Order creation status: {resp.status_code}")
    print(f">>> Order response: {resp.text}")
    assert resp.status_code == 201, f"Failed to create order: {resp.text}"
    data = resp.json()
    assert data["product_barcode"] == ORDER_ISSUED_SAMPLE["product_barcode"]
    assert data["quantity"] == ORDER_ISSUED_SAMPLE["quantity"]
    assert data["price_per_unit"] == ORDER_ISSUED_SAMPLE["price_per_unit"]
    assert data["status"] == "ISSUED"
    assert data["id"] is not None


def test_create_paid_order_success(client, auth_tokens):
    """Test creating a paid order"""
    resp = client.post(BASE_URL + "/orders/payfor", json=ORDER_PAID_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["product_barcode"] == ORDER_PAID_SAMPLE["product_barcode"]
    assert data["quantity"] == ORDER_PAID_SAMPLE["quantity"]
    assert data["status"] == "PAID"


def test_create_order_invalid_quantity(client, auth_tokens):
    """Test creating an order with invalid quantity"""
    invalid_order = {
        "product_barcode": "1234567890123",
        "quantity": -5,
        "price_per_unit": 29.99,
        "status": "ISSUED",
        "issue_date": None
    }
    resp = client.post(BASE_URL + "/orders", json=invalid_order, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 400


def test_create_order_invalid_price(client, auth_tokens):
    """Test creating an order with invalid price"""
    invalid_order = {
        "product_barcode": "1234567890123",
        "quantity": 5,
        "price_per_unit": -10.00,
        "status": "ISSUED",
        "issue_date": None
    }
    resp = client.post(BASE_URL + "/orders", json=invalid_order, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 400


def test_create_order_missing_fields(client, auth_tokens):
    """Test creating an order with missing required fields"""
    incomplete_order = {
        "product_barcode": "1234567890123",
        "quantity": 5
    }
    resp = client.post(BASE_URL + "/orders", json=incomplete_order, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code in (400, 422)


def test_create_order_nonexistent_product(client, auth_tokens):
    """Test creating an order for a non-existent product"""
    order = {
        "product_barcode": "9999999999999",
        "quantity": 5,
        "price_per_unit": 29.99,
        "status": "ISSUED",
        "issue_date": None
    }
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code in (400, 404)


def test_create_order_unauthenticated(client):
    """Test creating an order without authentication"""
    resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE)
    assert resp.status_code == 401


def test_create_order_forbidden_as_cashier(client, auth_tokens):
    """Test creating an order without proper authorization"""
    resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# LIST ORDERS TESTS
# ---------------------------

def test_list_orders_empty(client, auth_tokens):
    """Test listing orders when none exist"""
    resp = client.get(BASE_URL + "/orders", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_list_orders_after_creation(client, auth_tokens):
    """Test listing orders after creating multiple orders"""
    # Create a couple of orders
    client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    client.post(BASE_URL + "/orders/payfor", json=ORDER_PAID_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    
    resp = client.get(BASE_URL + "/orders", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_list_orders_unauthenticated(client):
    """Test listing orders without authentication"""
    resp = client.get(BASE_URL + "/orders")
    assert resp.status_code == 401


def test_list_orders_forbidden_as_cashier(client, auth_tokens):
    """Test listing orders without proper authorization"""
    resp = client.get(BASE_URL + "/orders", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# PAY ORDER TESTS
# ---------------------------

def test_pay_order_success(client, auth_tokens):
    """Test paying an issued order"""
    # First create an issued order
    create_resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    
    # Then pay it
    resp = client.patch(BASE_URL + f"/orders/{order_id}/pay", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True


def test_pay_order_invalid_id(client, auth_tokens):
    """Test paying an order with invalid ID"""
    resp = client.patch(BASE_URL + "/orders/-1/pay", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 400


def test_pay_order_nonexistent(client, auth_tokens):
    """Test paying a non-existent order"""
    resp = client.patch(BASE_URL + "/orders/99999/pay", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code in (400, 404)


def test_pay_order_unauthenticated(client):
    """Test paying an order without authentication"""
    resp = client.patch(BASE_URL + "/orders/1/pay")
    assert resp.status_code == 401


def test_pay_order_forbidden_as_cashier(client, auth_tokens):
    """Test paying an order without proper authorization"""
    resp = client.patch(BASE_URL + "/orders/1/pay", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# COMPLETE ORDER TESTS
# ---------------------------

def test_complete_order_success(client, auth_tokens):
    """Test completing a paid order"""
    # First create a paid order
    create_resp = client.post(BASE_URL + "/orders/payfor", json=ORDER_PAID_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    
    # Then complete it
    resp = client.patch(BASE_URL + f"/orders/{order_id}/arrival", headers=auth_header(auth_tokens, "admin"))
    print(f"\n>>> Complete order status: {resp.status_code}")
    print(f">>> Complete order response: {resp.text}")
    assert resp.status_code == 201, f"Failed to complete order: {resp.text}"
    data = resp.json()
    assert data["success"] is True


def test_complete_order_invalid_id(client, auth_tokens):
    """Test completing an order with invalid ID"""
    resp = client.patch(BASE_URL + "/orders/-1/arrival", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 400


def test_complete_order_nonexistent(client, auth_tokens):
    """Test completing a non-existent order"""
    resp = client.patch(BASE_URL + "/orders/99999/arrival", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code in (400, 404)


def test_complete_order_unauthenticated(client):
    """Test completing an order without authentication"""
    resp = client.patch(BASE_URL + "/orders/1/arrival")
    assert resp.status_code == 401


def test_complete_order_forbidden_as_cashier(client, auth_tokens):
    """Test completing an order without proper authorization"""
    resp = client.patch(BASE_URL + "/orders/1/arrival", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# ORDER STATUS WORKFLOW TESTS
# ---------------------------

def test_order_status_workflow_issued_to_paid(client, auth_tokens):
    """Test complete workflow: create issued order and pay it"""
    # Create issued order
    create_resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "ISSUED"
    
    # Pay the order
    pay_resp = client.patch(BASE_URL + f"/orders/{order_id}/pay", headers=auth_header(auth_tokens, "manager"))
    assert pay_resp.status_code == 201
    assert pay_resp.json()["success"] is True


def test_order_status_workflow_paid_to_completed(client, auth_tokens):
    """Test complete workflow: create paid order and complete it"""
    # Create paid order
    create_resp = client.post(BASE_URL + "/orders/payfor", json=ORDER_PAID_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "PAID"
    
    # Complete the order
    complete_resp = client.patch(BASE_URL + f"/orders/{order_id}/arrival", headers=auth_header(auth_tokens, "admin"))
    print(f"\n>>> Complete order status: {complete_resp.status_code}")
    print(f">>> Complete order response: {complete_resp.text}")
    assert complete_resp.status_code == 201, f"Failed to complete order: {complete_resp.text}"
    assert complete_resp.json()["success"] is True


# ---------------------------
# ORDER DATA INTEGRITY TESTS
# ---------------------------

def test_order_preserves_all_fields(client, auth_tokens):
    """Test that order creation preserves all fields correctly"""
    resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    
    assert data["product_barcode"] == ORDER_ISSUED_SAMPLE["product_barcode"]
    assert data["quantity"] == ORDER_ISSUED_SAMPLE["quantity"]
    assert data["price_per_unit"] == ORDER_ISSUED_SAMPLE["price_per_unit"]
    assert data["status"] == ORDER_ISSUED_SAMPLE["status"]
    assert data["id"] is not None
    assert data["id"] > 0


def test_order_returns_correct_response_structure(client, auth_tokens):
    """Test that order response has the correct structure"""
    resp = client.post(BASE_URL + "/orders", json=ORDER_ISSUED_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    
    # Check all required fields are present
    required_fields = ["id", "product_barcode", "quantity", "price_per_unit", "status"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
