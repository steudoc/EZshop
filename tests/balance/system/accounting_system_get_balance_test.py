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

def test_get_balance_success(client, setup_auth):
    """Test successfully retrieving balance after setting it"""
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


def test_get_balance_zero(client, setup_auth):
    """Test getting balance when it's zero"""
    # Set to zero
    client.post(
        BASE_URL + "/balance/set?amount=0.0",
        headers=auth_header(setup_auth)
    )
    
    # Get it
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0.0


def test_get_balance_positive_amount(client, setup_auth):
    """Test getting positive balance"""
    amount = 750.50
    
    client.post(
        BASE_URL + f"/balance/set?amount={amount}",
        headers=auth_header(setup_auth)
    )
    
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 200
    assert resp.json()["balance"] == amount


def test_get_balance_returns_latest(client, setup_auth):
    """Test that get_balance returns the latest value after multiple sets"""
    amounts = [100.0, 250.0, 500.0]
    
    for amount in amounts:
        client.post(
            BASE_URL + f"/balance/set?amount={amount}",
            headers=auth_header(setup_auth)
        )
    
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 200
    # Should return the last set amount
    assert resp.json()["balance"] == 500.0

def test_get_balance_unauthenticated(client):
    """Test that unauthenticated request is rejected"""
    resp = client.get(BASE_URL + "/balance")
    
    assert resp.status_code == 401


def test_get_balance_without_header(client):
    """Test that request without auth header is rejected"""
    resp = client.get(
        BASE_URL + "/balance",
        headers={"Authorization": ""}
    )
    
    assert resp.status_code == 401


def test_get_balance_invalid_token(client):
    """Test that request with invalid token is rejected"""
    resp = client.get(
        BASE_URL + "/balance",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )
    
    assert resp.status_code == 401

def test_get_balance_in_complete_workflow(client, setup_auth):
    """Test get_balance in complete workflow: set -> get -> reset -> get"""
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


def test_get_balance_consistency(client, setup_auth):
    """Test that get_balance returns consistent values"""
    # Set balance
    client.post(
        BASE_URL + "/balance/set?amount=555.55",
        headers=auth_header(setup_auth)
    )
    
    # Get and verify consistency
    values = []
    for _ in range(5):
        resp = client.get(
            BASE_URL + "/balance",
            headers=auth_header(setup_auth)
        )
        assert resp.status_code == 200
        values.append(resp.json()["balance"])
    
    # All values should be identical
    assert len(set(values)) == 1
    assert values[0] == 555.55
