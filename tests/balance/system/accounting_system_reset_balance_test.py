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

def test_reset_balance_verifies_zero(client, setup_auth):
    """Test that balance is actually zero after reset"""
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
    
    # Get balance and verify it's zero
    resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0.0


def test_reset_balance_from_positive(client, setup_auth):
    """Test resetting balance from positive amount"""
    client.post(
        BASE_URL + "/balance/set?amount=250.50",
        headers=auth_header(setup_auth)
    )
    
    resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 205


def test_reset_balance_from_zero(client, setup_auth):
    """Test resetting balance that's already zero"""
    # Set to zero
    client.post(
        BASE_URL + "/balance/set?amount=0.0",
        headers=auth_header(setup_auth)
    )
    
    # Reset (should still work)
    resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    assert resp.status_code == 205

def test_reset_balance_unauthenticated(client):
    """Test that unauthenticated request is rejected"""
    resp = client.post(BASE_URL + "/balance/reset")
    
    assert resp.status_code == 401


def test_reset_balance_invalid_token(client):
    """Test that request with invalid token is rejected"""
    resp = client.post(
        BASE_URL + "/balance/reset",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    
    assert resp.status_code == 401


def test_reset_without_prior_set(client, setup_auth):
    """Test reset when no balance has been explicitly set"""
    # Just call reset without setting anything first
    resp = client.post(
        BASE_URL + "/balance/reset",
        headers=auth_header(setup_auth)
    )
    
    # Should still work
    assert resp.status_code == 205
    
    # Verify balance is zero
    get_resp = client.get(
        BASE_URL + "/balance",
        headers=auth_header(setup_auth)
    )
    assert get_resp.json()["balance"] == 0.0