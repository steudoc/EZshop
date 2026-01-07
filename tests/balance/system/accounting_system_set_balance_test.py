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

def test_set_balance_success(client, setup_auth):
    """Test successfully setting balance with positive amount"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=1000.0",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 201
    data = resp.json()
    assert "success" in data
    assert data["success"] is True


def test_set_balance_zero(client, setup_auth):
    """Test setting balance to zero"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=0.0",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True


def test_set_balance_negative_rejected(client, setup_auth):
    """Test that negative balance is rejected"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=-100.0",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 421

def test_set_balance_then_get(client, setup_auth):
    """Test that balance is correctly set and retrievable"""
    amount = 555.55
    
    # Set balance
    set_resp = client.post(
        BASE_URL + f"/balance/set?amount={amount}",
        headers=auth_header(setup_auth)
    )
    assert set_resp.status_code == 201
    
    # Get balance and verify
    get_resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["balance"] == amount


def test_set_balance_overwrites_previous(client, setup_auth):
    """Test that new set_balance overwrites previous balance"""
    # Set first balance
    client.post(
        BASE_URL + "/balance/set?amount=100.0",
        headers=auth_header(setup_auth)
    )
    
    # Set second balance
    client.post(
        BASE_URL + "/balance/set?amount=200.0",
        headers=auth_header(setup_auth)
    )
    
    # Verify second balance is active
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == 200.0


def test_set_balance_unauthenticated(client):
    """Test that unauthenticated request is rejected"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=100.0"
    )
    
    assert resp.status_code == 401


def test_set_balance_without_header(client):
    """Test that request without auth header is rejected"""
    resp = client.post(
        BASE_URL + "/balance/set?amount=100.0",
        headers={"Authorization": ""}
    )
    
    assert resp.status_code == 401
