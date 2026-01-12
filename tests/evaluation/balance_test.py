import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from init_db import reset, init_db
import asyncio

# ---------------------------
# PYTEST CONFIGURATION
# ---------------------------

pytestmark = pytest.mark.asyncio

# ---------------------------
# FIXTURES
# ---------------------------

@pytest.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(autouse=True)
async def reset_state():
    """
    Ensure a clean API-visible state before each test.
    No DB internals are asserted.
    """
    await reset()
    await init_db()


@pytest.fixture(scope="session")
def initial_users():
    return {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }


@pytest.fixture
async def auth_tokens(client, initial_users):
    tokens = {}
    for role, creds in initial_users.items():
        resp = await client.post(
            "/api/v1/auth",
            json=creds,
            follow_redirects=True,
        )
        assert resp.status_code == 200
        tokens[role] = f"Bearer {resp.json()['token']}"
    return tokens


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}

# ---------------------------
# HELPERS
# ---------------------------

async def get_balance(client, auth_tokens):
    resp = await client.get(
        "/api/v1/balance",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    return resp.json()['balance']

async def set_balance(client, auth_tokens, amount: float):
    resp = await client.post(
        f"/api/v1/balance/set?amount={int(amount)}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201

# ---------------------------
# POST /balance/reset — SUCCESS
# ---------------------------

async def test_reset_balance_success(client, auth_tokens):
    await set_balance(client, auth_tokens, 100.0)

    resp = await client.post(
        "/api/v1/balance/reset",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 205

    balance = await get_balance(client, auth_tokens)
    assert balance == 0.0

# ---------------------------
# POST /balance/reset — AUTH
# ---------------------------

async def test_reset_balance_no_auth(client):
    resp = await client.post(
        "/api/v1/balance/reset",
        follow_redirects=True,
    )
    assert resp.status_code == 401

async def test_reset_balance_invalid_token(client):
    resp = await client.post(
        "/api/v1/balance/reset",
        headers={"Authorization": "Bearer invalid"},
        follow_redirects=True,
    )
    assert resp.status_code == 401

@pytest.mark.parametrize("role", ["manager", "cashier"])
async def test_reset_balance_forbidden_role(client, auth_tokens, role):
    resp = await client.post(
        "/api/v1/balance/reset",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 403

# ---------------------------
# POST /balance/set — SUCCESS
# ---------------------------

async def test_set_balance_success(client, auth_tokens):
    amount = 50
    resp = await client.post(
        f"/api/v1/balance/set?amount={amount}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201

    balance = await get_balance(client, auth_tokens)
    assert balance == float(amount)

# ---------------------------
# POST /balance/set — BAD REQUEST
# ---------------------------

async def test_set_balance_negative_amount(client, auth_tokens):
    resp = await client.post(
        "/api/v1/balance/set?amount=-1.0",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 421

# ---------------------------
# POST /balance/set — AUTH
# ---------------------------

async def test_set_balance_no_auth(client):
    resp = await client.post(
        "/api/v1/balance/set?amount=10.0",
        follow_redirects=True,
    )
    assert resp.status_code == 401

async def test_set_balance_invalid_token(client):
    resp = await client.post(
        "/api/v1/balance/set?amount=10.0",
        headers={"Authorization": "Bearer invalid"},
        follow_redirects=True,
    )
    assert resp.status_code == 401

@pytest.mark.parametrize("role", ["manager", "cashier"])
async def test_set_balance_forbidden_role(client, auth_tokens, role):
    resp = await client.post(
        f"/api/v1/balance/set?amount=10.0",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 403

# ---------------------------
# GET /balance — SUCCESS
# ---------------------------

async def test_get_balance_success(client, auth_tokens):
    resp = await client.get(
        "/api/v1/balance",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    data = resp.json()['balance']
    assert isinstance(data, float)

# ---------------------------
# GET /balance — AUTH
# ---------------------------

@pytest.mark.asyncio
async def test_get_balance_no_auth(client):
    resp = await client.get(
        "/api/v1/balance",
        follow_redirects=True,
    )
    assert resp.status_code == 401

async def test_get_balance_invalid_token(client):
    resp = await client.get(
        "/api/v1/balance",
        headers={"Authorization": "Bearer invalid"},
        follow_redirects=True,
    )
    assert resp.status_code == 401

@pytest.mark.parametrize("role", ["manager", "cashier"])
async def test_get_balance_forbidden_role(client, auth_tokens, role):
    resp = await client.get(
        "/api/v1/balance",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 403