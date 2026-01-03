import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db


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
# GLOBAL FIXTURE FOR SETUP
# ---------------------------

@pytest.fixture(scope="session", autouse=True)
def setup(event_loop, client):
    """Initialize database and create test data."""
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
    
    # Initialize system balance
    balance_resp = client.post(BASE_URL + "/balance/set?amount=50000", headers=auth_header(tokens, "admin"))
    assert balance_resp.status_code == 201, f"Failed to set balance: {balance_resp.text}"
    
    # Create test products
    products = [
        {
            "barcode": "5901234123457",
            "description": "Laptop",
            "price_per_unit": 999.99,
            "quantity": 10,
            "position": "1-A-1"
        },
        {
            "barcode": "5901234123464",
            "description": "Mouse",
            "price_per_unit": 29.99,
            "quantity": 100,
            "position": "2-B-2"
        },
        {
            "barcode": "5901234123471",
            "description": "Keyboard",
            "price_per_unit": 79.99,
            "quantity": 50,
            "position": "3-C-3"
        }
    ]
    
    for product in products:
        resp = client.post(BASE_URL + "/products", json=product, headers=auth_header(tokens, "admin"))
        assert resp.status_code == 201, f"Failed to create product: {resp.text}"
    
    return {"tokens": tokens, "products": products}


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}


# ---------------------------
# SCENARIO: Shop Manager creates and manages orders
# ---------------------------

def test_manager_creates_issued_order(client, setup):
    """Shop Manager creates an order that needs to be paid"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "5901234123457",
        "quantity": 2,
        "price_per_unit": 999.99,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "ISSUED"
    assert data["product_barcode"] == "5901234123457"
    assert data["quantity"] == 2


def test_manager_can_view_all_orders(client, setup):
    """Shop Manager can view all orders in the system"""
    tokens = setup["tokens"]
    
    resp = client.get(BASE_URL + "/orders", headers=auth_header(tokens, "manager"))
    assert resp.status_code == 200
    orders = resp.json()
    assert isinstance(orders, list)
    # Should have at least the order created above
    assert len(orders) >= 1


def test_manager_pays_issued_order(client, setup):
    """Shop Manager pays an ISSUED order"""
    tokens = setup["tokens"]
    
    # Create an issued order
    order = {
        "product_barcode": "5901234123464",
        "quantity": 5,
        "price_per_unit": 29.99,
        "status": "ISSUED",
        "issue_date": None
    }
    create_resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    
    # Pay the order
    pay_resp = client.patch(BASE_URL + f"/orders/{order_id}/pay", headers=auth_header(tokens, "manager"))
    assert pay_resp.status_code == 201
    assert pay_resp.json()["success"] is True


# ---------------------------
# SCENARIO: Administrator creates paid orders directly
# ---------------------------

def test_admin_creates_paid_order_directly(client, setup):
    """Administrator can create an order and pay it immediately"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "5901234123471",
        "quantity": 3,
        "price_per_unit": 79.99,
        "status": "PAID",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders/payfor", json=order, headers=auth_header(tokens, "admin"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "PAID"
    assert data["product_barcode"] == "5901234123471"


def test_admin_completes_paid_order(client, setup):
    """Administrator marks a PAID order as COMPLETED when items arrive"""
    tokens = setup["tokens"]
    
    # Create a paid order
    order = {
        "product_barcode": "5901234123457",
        "quantity": 1,
        "price_per_unit": 999.99,
        "status": "PAID",
        "issue_date": None
    }
    create_resp = client.post(BASE_URL + "/orders/payfor", json=order, headers=auth_header(tokens, "admin"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    
    # Complete the order on arrival
    complete_resp = client.patch(BASE_URL + f"/orders/{order_id}/arrival", headers=auth_header(tokens, "admin"))
    assert complete_resp.status_code == 201
    assert complete_resp.json()["success"] is True


# ---------------------------
# SCENARIO: Complete order lifecycle
# ---------------------------

def test_complete_order_lifecycle_issued_to_paid_to_completed(client, setup):
    """Test the complete lifecycle: ISSUED -> PAID -> COMPLETED"""
    tokens = setup["tokens"]
    
    # Step 1: Manager creates an ISSUED order
    order = {
        "product_barcode": "5901234123464",
        "quantity": 10,
        "price_per_unit": 29.99,
        "status": "ISSUED",
        "issue_date": None
    }
    create_resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "ISSUED"
    
    # Step 2: Manager pays the ISSUED order
    pay_resp = client.patch(BASE_URL + f"/orders/{order_id}/pay", headers=auth_header(tokens, "manager"))
    assert pay_resp.status_code == 201
    
    # Step 3: Admin completes the order on arrival
    complete_resp = client.patch(BASE_URL + f"/orders/{order_id}/arrival", headers=auth_header(tokens, "admin"))
    assert complete_resp.status_code == 201
    assert complete_resp.json()["success"] is True


def test_complete_order_lifecycle_paid_direct_to_completed(client, setup):
    """Test direct workflow: PAID (created directly) -> COMPLETED"""
    tokens = setup["tokens"]
    
    # Step 1: Admin creates a PAID order directly
    order = {
        "product_barcode": "5901234123471",
        "quantity": 5,
        "price_per_unit": 79.99,
        "status": "PAID",
        "issue_date": None
    }
    create_resp = client.post(BASE_URL + "/orders/payfor", json=order, headers=auth_header(tokens, "admin"))
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "PAID"
    
    # Step 2: Admin completes the order on arrival
    complete_resp = client.patch(BASE_URL + f"/orders/{order_id}/arrival", headers=auth_header(tokens, "admin"))
    assert complete_resp.status_code == 201
    assert complete_resp.json()["success"] is True


# ---------------------------
# SCENARIO: Access control and authorization
# ---------------------------

def test_cashier_cannot_create_order(client, setup):
    """Cashier should not be able to create orders"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "5901234123457",
        "quantity": 1,
        "price_per_unit": 999.99,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "cashier"))
    assert resp.status_code == 403


def test_cashier_cannot_list_orders(client, setup):
    """Cashier should not be able to list orders"""
    tokens = setup["tokens"]
    
    resp = client.get(BASE_URL + "/orders", headers=auth_header(tokens, "cashier"))
    assert resp.status_code == 403


def test_cashier_cannot_pay_order(client, setup):
    """Cashier should not be able to pay orders"""
    tokens = setup["tokens"]
    
    resp = client.patch(BASE_URL + "/orders/1/pay", headers=auth_header(tokens, "cashier"))
    assert resp.status_code == 403


def test_unauthenticated_cannot_create_order(client):
    """Unauthenticated users cannot create orders"""
    order = {
        "product_barcode": "5901234123457",
        "quantity": 1,
        "price_per_unit": 999.99,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order)
    assert resp.status_code == 401


# ---------------------------
# SCENARIO: Error handling and validation
# ---------------------------

def test_cannot_create_order_with_zero_quantity(client, setup):
    """Cannot create order with zero or negative quantity"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "5901234123457",
        "quantity": 0,
        "price_per_unit": 999.99,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert resp.status_code == 400


def test_cannot_create_order_with_negative_price(client, setup):
    """Cannot create order with negative price"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "5901234123457",
        "quantity": 1,
        "price_per_unit": -100.0,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert resp.status_code == 400


def test_cannot_create_order_with_nonexistent_product(client, setup):
    """Cannot create order for non-existent product"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "9999999999999",
        "quantity": 1,
        "price_per_unit": 99.99,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert resp.status_code in (400, 404)


def test_cannot_pay_nonexistent_order(client, setup):
    """Cannot pay a non-existent order"""
    tokens = setup["tokens"]
    
    resp = client.patch(BASE_URL + "/orders/99999/pay", headers=auth_header(tokens, "manager"))
    assert resp.status_code in (400, 404)


def test_cannot_complete_nonexistent_order(client, setup):
    """Cannot complete a non-existent order"""
    tokens = setup["tokens"]
    
    resp = client.patch(BASE_URL + "/orders/99999/arrival", headers=auth_header(tokens, "admin"))
    assert resp.status_code in (400, 404)


# ---------------------------
# SCENARIO: Business logic - balance management
# ---------------------------

def test_system_balance_decreases_when_order_is_paid(client, setup):
    """System balance should decrease when a PAID order is created"""
    tokens = setup["tokens"]
    
    # Get initial balance
    initial_balance_resp = client.get(BASE_URL + "/balance", headers=auth_header(tokens, "admin"))
    assert initial_balance_resp.status_code == 200
    initial_balance = initial_balance_resp.json()["balance"]
    
    # Create a PAID order
    order = {
        "product_barcode": "5901234123457",
        "quantity": 1,
        "price_per_unit": 999.99,
        "status": "PAID",
        "issue_date": None
    }
    resp = client.post(BASE_URL + "/orders/payfor", json=order, headers=auth_header(tokens, "admin"))
    assert resp.status_code == 201
    
    # Check balance decreased
    final_balance_resp = client.get(BASE_URL + "/balance", headers=auth_header(tokens, "admin"))
    assert final_balance_resp.status_code == 200
    final_balance = final_balance_resp.json()["balance"]
    
    expected_decrease = 1 * 999.99
    assert final_balance == initial_balance - expected_decrease


def test_cannot_create_paid_order_with_insufficient_balance(client, setup):
    """Cannot create PAID order if system balance is insufficient"""
    tokens = setup["tokens"]
    
    # Set balance to a low amount
    client.post(BASE_URL + "/balance/set?amount=10", headers=auth_header(tokens, "admin"))
    
    # Try to create expensive PAID order
    order = {
        "product_barcode": "5901234123457",
        "quantity": 1,
        "price_per_unit": 999.99,
        "status": "PAID",
        "issue_date": None
    }
    resp = client.post(BASE_URL + "/orders/payfor", json=order, headers=auth_header(tokens, "admin"))
    assert resp.status_code == 421  # BalanceError returns 421
    
    # Reset balance for other tests
    client.post(BASE_URL + "/balance/set?amount=50000", headers=auth_header(tokens, "admin"))


# ---------------------------
# SCENARIO: Multiple orders from different users
# ---------------------------

def test_multiple_managers_can_create_orders(client, setup):
    """Multiple shop managers should be able to create orders"""
    tokens = setup["tokens"]
    
    # Create multiple orders
    for i in range(3):
        order = {
            "product_barcode": "5901234123464",
            "quantity": i + 1,
            "price_per_unit": 29.99,
            "status": "ISSUED",
            "issue_date": None
        }
        resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
        assert resp.status_code == 201
    
    # Verify all orders are listed
    list_resp = client.get(BASE_URL + "/orders", headers=auth_header(tokens, "manager"))
    assert list_resp.status_code == 200
    orders = list_resp.json()
    assert len(orders) >= 3


def test_orders_preserve_all_information(client, setup):
    """Orders should preserve all provided information accurately"""
    tokens = setup["tokens"]
    
    order = {
        "product_barcode": "5901234123471",
        "quantity": 7,
        "price_per_unit": 79.99,
        "status": "ISSUED",
        "issue_date": None
    }
    
    resp = client.post(BASE_URL + "/orders", json=order, headers=auth_header(tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    
    # Verify all fields
    assert data["product_barcode"] == order["product_barcode"]
    assert data["quantity"] == order["quantity"]
    assert data["price_per_unit"] == order["price_per_unit"]
    assert data["status"] == order["status"]
    assert data["id"] is not None
    assert data["id"] > 0
