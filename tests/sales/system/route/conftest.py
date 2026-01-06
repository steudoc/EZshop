import asyncio
import pytest
from fastapi.testclient import TestClient
from init_db import reset, init_db
from utils_route import BASE_URL, auth_header

# ---------------------------
# GLOBAL FIXTURE
# ---------------------------

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


@pytest.fixture(autouse=True)
def fresh_db(event_loop):
    # BEFORE each test
    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
    yield
    # AFTER each test
    #event_loop.run_until_complete(reset())


@pytest.fixture
def auth_tokens(client):
    users = {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }

    tokens = {}
    for role, creds in users.items():
        response = client.post(BASE_URL + "/auth", json=creds)
        assert response.status_code == 200
        tokens[role] = f"Bearer {response.json()['token']}"

    return tokens

@pytest.fixture(autouse=True)
def set_system_balance(client, auth_tokens):
    """
    Ensure system balance is set before each test.
    Requires admin privileges.
    """
    amount = 10000.0
    resp = client.post(
        f"{BASE_URL}/balance/set?amount={amount}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    yield