"""
Acceptance tests for Balance API endpoints.

Tests the complete HTTP API for balance operations including:
- GET /api/v1/balance - Retrieve current balance
- POST /api/v1/balance/set - Set balance to a specific amount
- POST /api/v1/balance/reset - Reset balance to zero

Uses FastAPI TestClient to make real HTTP requests to the application.
"""

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
    with TestClient(app) as c:
        yield c


BASE_URL = "http://127.0.0.1:8000/api/v1"


@pytest.fixture(scope="session", autouse=True)
def setup_auth(event_loop, client):
    """Setup database and authenticate admin user once."""
    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
    
    # Login as admin
    response = client.post(
        BASE_URL + "/auth",
        json={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    token = f"Bearer {response.json()['token']}"
    return token


def auth_header(token: str):
    """Helper to create authorization header"""
    return {"Authorization": token}


# ---------------------------
# SET BALANCE TESTS
# ---------------------------

def test_set_balance_success(client, setup_auth):
    """Test successfully setting balance"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=100.0",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True


def test_set_balance_zero(client, setup_auth):
    """Test setting balance to zero"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=0.0",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True


def test_set_balance_large_amount(client, setup_auth):
    """Test setting a large balance"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=999999.99",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True


def test_set_balance_decimal_precision(client, setup_auth):
    """Test setting balance with decimal precision"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=123.456",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True
    
    # Verify the balance was set correctly
    balance_resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert balance_resp.status_code == 200
    assert abs(balance_resp.json()["balance"] - 123.456) < 0.001


def test_set_balance_negative_raises_error(client, setup_auth):
    """Test that setting negative balance raises error"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=-100.0",
        headers=auth_header(setup_auth)
    )
    # Should return 421 or error status
    assert resp.status_code >= 400


def test_set_balance_unauthenticated(client):
    """Test that unauthenticated request is rejected"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=100.0"
    )
    assert resp.status_code == 401


def test_set_balance_sequential_updates(client, setup_auth):
    """Test multiple sequential balance updates"""
    amounts = [50.0, 150.0, 250.0]
    
    for amount in amounts:
        resp = client.post(
            BASE_URL + f"/balance/set?amount={amount}",
            headers=auth_header(setup_auth)
        )
        assert resp.status_code == 201
        assert resp.json()["success"] is True
    
    # Verify final balance
    balance_resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert balance_resp.status_code == 200
    assert balance_resp.json()["balance"] == 250.0


# ---------------------------
# GET BALANCE TESTS
# ---------------------------

def test_get_balance_success(client, setup_auth):
    """Test successfully retrieving balance"""
    # First set a balance
    client.post(
        BASE_URL + "/balance/set?amount=500.0",
        headers=auth_header(setup_auth)
    )
    
    # Then get it
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "balance" in data
    assert data["balance"] == 500.0


def test_get_balance_after_reset(client, setup_auth):
    """Test getting balance after reset"""
    # Set a balance
    client.post(
        BASE_URL + "/balance/set?amount=300.0",
        headers=auth_header(setup_auth)
    )
    
    # Reset it
    client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    # Get balance
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0.0


def test_get_balance_multiple_calls(client, setup_auth):
    """Test that multiple get calls return same value"""
    # Set a balance
    client.post(
        BASE_URL + "/balance/set?amount=777.77",
        headers=auth_header(setup_auth)
    )
    
    # Get multiple times
    resp1 = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    resp2 = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    resp3 = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 200
    
    assert resp1.json()["balance"] == resp2.json()["balance"] == resp3.json()["balance"]


def test_get_balance_unauthenticated(client):
    """Test that unauthenticated request is rejected"""
    resp = client.get(BASE_URL + "/balance")
    assert resp.status_code == 401


def test_get_balance_returns_json(client, setup_auth):
    """Test that response is valid JSON"""
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 200
    
    # Should be able to parse as JSON
    data = resp.json()
    assert isinstance(data, dict)
    assert "balance" in data


def test_get_balance_response_format(client, setup_auth):
    """Test response format contains required fields"""
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 200
    
    data = resp.json()
    assert isinstance(data["balance"], (int, float))


# ---------------------------
# RESET BALANCE TESTS
# ---------------------------

def test_reset_balance_success(client, setup_auth):
    """Test successfully resetting balance"""
    # Set a balance first
    client.post(
        BASE_URL + "/balance/set?amount=1000.0",
        headers=auth_header(setup_auth)
    )
    
    # Reset it
    resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 205


def test_reset_balance_returns_empty(client, setup_auth):
    """Test that reset returns empty response (status 205)"""
    client.post(
        BASE_URL + "/balance/set?amount=500.0",
        headers=auth_header(setup_auth)
    )
    
    resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 205
    # Status 205 should return empty or minimal content
    assert len(resp.text) == 0 or resp.text.isspace()


def test_reset_balance_idempotent(client, setup_auth):
    """Test that reset can be called multiple times"""
    client.post(
        BASE_URL + "/balance/set?amount=100.0",
        headers=auth_header(setup_auth)
    )
    
    # Reset multiple times
    resp1 = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    resp2 = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    resp3 = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    assert resp1.status_code == 205
    assert resp2.status_code == 205
    assert resp3.status_code == 205


def test_reset_balance_verifies_zero(client, setup_auth):
    """Test that balance is actually zero after reset"""
    # Set balance
    client.post(
        BASE_URL + "/balance/set?amount=750.0",
        headers=auth_header(setup_auth)
    )
    
    # Reset
    client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    # Verify it's zero
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0.0


def test_reset_balance_unauthenticated(client):
    """Test that unauthenticated request is rejected"""
    resp = client.post(BASE_URL + "/balance/reset")
    assert resp.status_code == 401


def test_reset_balance_and_set_after(client, setup_auth):
    """Test setting balance after reset works correctly"""
    # Set initial balance
    client.post(
        BASE_URL + "/balance/set?amount=100.0",
        headers=auth_header(setup_auth)
    )
    
    # Reset
    client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    # Set new balance
    resp = client.post(
        BASE_URL + "/balance/set?amount=999.0",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 201
    
    # Verify new balance
    balance_resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert balance_resp.json()["balance"] == 999.0


# ---------------------------
# WORKFLOW TESTS
# ---------------------------

def test_complete_balance_workflow(client, setup_auth):
    """Test complete workflow: set -> get -> reset -> get"""
    # Set balance
    set_resp = client.post(
        BASE_URL + "/balance/set?amount=250.0",
        headers=auth_header(setup_auth)
    )
    assert set_resp.status_code == 201
    
    # Get balance
    get_resp1 = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert get_resp1.status_code == 200
    assert get_resp1.json()["balance"] == 250.0
    
    # Reset balance
    reset_resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    assert reset_resp.status_code == 205
    
    # Get balance again
    get_resp2 = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert get_resp2.status_code == 200
    assert get_resp2.json()["balance"] == 0.0


def test_multiple_operations_sequence(client, setup_auth):
    """Test sequence of operations: set -> get -> set -> get -> reset -> get"""
    amounts = [100.0, 250.0, 500.0]
    
    for amount in amounts:
        # Set
        set_resp = client.post(
            BASE_URL + f"/balance/set?amount={amount}",
            headers=auth_header(setup_auth)
        )
        assert set_resp.status_code == 201
        
        # Get and verify
        get_resp = client.get(
            BASE_URL + "/balance",
            headers=auth_header(setup_auth)
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["balance"] == amount
    
    # Final reset
    reset_resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    assert reset_resp.status_code == 205
    
    # Verify reset
    final_get = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert final_get.json()["balance"] == 0.0
