import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from init_db import reset, init_db

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
async def auth_tokens(client, initial_users, reset_state):
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

async def create_product(client, auth_tokens):
    payload = {
        "description": "Water Bottle",
        "barcode": "036000291452",
        "price_per_unit": 1.50,
    }
    resp = await client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    return resp.json()

async def locate_product(client, auth_tokens, id: int):
    resp = await client.patch(
        f"/api/v1/products/{id}/position?position=1-B-1",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201

async def create_order(client, auth_tokens):
    product = await create_product(client, auth_tokens)

    resp = await client.post(
        "/api/v1/orders",
        json={
            "product_barcode": product["barcode"],
            "quantity": 1,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    return resp.json()

async def create_paid_order(client, auth_tokens, located : bool = True):
    product = await create_product(client, auth_tokens)
    if located:
        await locate_product(client, auth_tokens, product["id"])
    await set_balance(client, auth_tokens, 100.0)

    resp = await client.post(
        "/api/v1/orders/payfor",
        json={
            "product_barcode": product["barcode"],
            "quantity": 1,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    return resp.json()

async def set_balance(client, auth_tokens, amount: float):
    resp = await client.post(
        f"/api/v1/balance/set?amount={amount}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201

def valid_order_payload(barcode):
    return {
        "product_barcode": barcode,
        "quantity": 10,
        "price_per_unit": 5.0,
    }


# ---------------------------
# POST /orders — SUCCESS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_issue_order_success(client, auth_tokens, role):
    product = await create_product(client, auth_tokens)

    resp = await client.post(
        "/api/v1/orders",
        json=valid_order_payload(product["barcode"]),
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    assert resp.json().get('id') is not None
    assert resp.json().get('status') == 'ISSUED'

async def test_issue_order_ignores_provided_id(client, auth_tokens):
    product = await create_product(client, auth_tokens)

    payload = valid_order_payload(product["barcode"]) | {"id": 999}

    resp = await client.post(
        "/api/v1/orders",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    assert resp.json().get("id") != 999
    assert resp.json().get('status') == 'ISSUED'


# ---------------------------
# POST /orders — BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("payload", [
    {},  # missing everything
    {"quantity": 1, "price_per_unit": 5.0},
    {"barcode": "", "quantity": 1, "price_per_unit": 5.0},
    {"barcode": "123", "quantity": 1, "price_per_unit": 5.0},
    {"barcode": "8058269191689", "quantity": 0, "price_per_unit": 5.0},
    {"barcode": "8058269191689", "quantity": -1, "price_per_unit": 5.0},
    {"barcode": "8058269191689", "quantity": 1, "price_per_unit": 0},
    {"barcode": "8058269191689", "quantity": 1, "price_per_unit": -1},
])
async def test_issue_order_bad_request(client, auth_tokens, payload):
    resp = await client.post(
        "/api/v1/orders",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)


# ---------------------------
# POST /orders — NOT FOUND
# ---------------------------

async def test_issue_order_product_not_found(client, auth_tokens):
    payload = valid_order_payload("8058269191689")

    resp = await client.post(
        "/api/v1/orders",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


# ---------------------------
# POST /orders — AUTH
# ---------------------------

async def test_issue_order_no_auth(client):
    resp = await client.post(
        "/api/v1/orders",
        json={"barcode": "8058269191689", "quantity": 1, "price_per_unit": 5.0},
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_issue_order_invalid_token(client):
    resp = await client.post(
        "/api/v1/orders",
        json={"barcode": "8058269191689", "quantity": 1, "price_per_unit": 5.0},
        headers={"Authorization": "Bearer invalid"},
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_issue_order_forbidden_role(client, auth_tokens):
    resp = await client.post(
        "/api/v1/orders",
        json={"barcode": "8058269191689", "quantity": 1, "price_per_unit": 5.0},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403


# ---------------------------
# GET /orders — SUCCESS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_list_orders_success(client, auth_tokens, role):
    resp = await client.get(
        "/api/v1/orders",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_orders_with_data(client, auth_tokens):
    product = await create_product(client, auth_tokens)

    await client.post(
        "/api/v1/orders",
        json=valid_order_payload(product["barcode"]),
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    resp = await client.get(
        "/api/v1/orders",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ---------------------------
# GET /orders — AUTH
# ---------------------------

async def test_list_orders_no_auth(client):
    resp = await client.get(
        "/api/v1/orders",
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_list_orders_invalid_token(client):
    resp = await client.get(
        "/api/v1/orders",
        headers={"Authorization": "Bearer invalid"},
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_list_orders_forbidden_role(client, auth_tokens):
    resp = await client.get(
        "/api/v1/orders",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

# ---------------------------
# POST /orders/payfor — SUCCESS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_payfor_order_success(client, auth_tokens, role):
    product = await create_product(client, auth_tokens)
    await set_balance(client, auth_tokens, 100.0)

    resp = await client.post(
        "/api/v1/orders/payfor",
        json={
            "product_barcode": product["barcode"],
            "quantity": 10,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201

async def test_payfor_order_ignores_id(client, auth_tokens):
    product = await create_product(client, auth_tokens)
    res = await set_balance(client, auth_tokens, 100.0)

    resp = await client.post(
        "/api/v1/orders/payfor",
        json={
            "id": 999,
            "product_barcode": product["barcode"],
            "quantity": 1,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    assert resp.json().get("id") != 999

# ---------------------------
# POST /orders — BAD REQUEST 
# ---------------------------

@pytest.mark.parametrize("payload", [
    {},
    {"quantity": 1, "price_per_unit": 5.0},
    {"product_barcode": "", "quantity": 1, "price_per_unit": 5.0},
    {"product_barcode": "123", "quantity": 1, "price_per_unit": 5.0},
    {"product_barcode": "8058269191689", "quantity": 0, "price_per_unit": 5.0},
    {"product_barcode": "8058269191689", "quantity": -1, "price_per_unit": 5.0},
])
async def test_payfor_order_bad_request(client, auth_tokens, payload):
    resp = await client.post(
        "/api/v1/orders/payfor",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_payfor_order_product_not_found(client, auth_tokens):
    await set_balance(client, auth_tokens, 100.0)

    resp = await client.post(
        "/api/v1/orders/payfor",
        json={
            "product_barcode": "8058269191689",
            "quantity": 1,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


async def test_payfor_order_no_auth(client):
    resp = await client.post(
        "/api/v1/orders/payfor",
        json={"product_barcode": "8058269191689", "quantity": 1, "price_per_unit": 5.0},
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_payfor_order_forbidden(client, auth_tokens):
    resp = await client.post(
        "/api/v1/orders/payfor",
        json={"product_barcode": "8058269191689", "quantity": 1, "price_per_unit": 5.0},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403


async def test_payfor_order_insufficient_balance(client, auth_tokens):
    product = await create_product(client, auth_tokens)

    resp = await client.post(
        "/api/v1/orders/payfor",
        json={
            "product_barcode": product["barcode"],
            "quantity": 10,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 421

# ---------------------------
# PATCH /orders/{order_id}/pay — SUCCESS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_pay_order_success(client, auth_tokens, role):
    order = await create_order(client, auth_tokens)
    await set_balance(client, auth_tokens, 100.0)

    resp = await client.patch(
        f"/api/v1/orders/{order['id']}/pay",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201

@pytest.mark.parametrize("order_id", [-1, "abc"])
async def test_pay_order_invalid_id(client, auth_tokens, order_id):
    resp = await client.patch(
        f"/api/v1/orders/{order_id}/pay",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_pay_order_not_found(client, auth_tokens):
    await set_balance(client, auth_tokens, 100.0)

    resp = await client.patch(
        "/api/v1/orders/999999/pay",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


async def test_pay_order_no_auth(client):
    resp = await client.patch(
        "/api/v1/orders/1/pay",
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_pay_order_forbidden(client, auth_tokens):
    resp = await client.patch(
        "/api/v1/orders/1/pay",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

async def test_pay_order_already_paid(client, auth_tokens):
    product = await create_product(client, auth_tokens)
    await set_balance(client, auth_tokens, 100.0)

    paid = await client.post(
        "/api/v1/orders/payfor",
        json={
            "product_barcode": product["barcode"],
            "quantity": 1,
            "price_per_unit": 5.0,
        },
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert paid.status_code == 201

    resp = await client.patch(
        f"/api/v1/orders/{paid.json()['id']}/pay",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420

# ---------------------------
# PATCH /orders/{order_id}/arrival — SUCCESS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_order_arrival_success(client, auth_tokens, role):
    order = await create_paid_order(client, auth_tokens)

    resp = await client.patch(
        f"/api/v1/orders/{order['id']}/arrival",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201


@pytest.mark.parametrize("order_id", [-1, "abc"])
async def test_order_arrival_invalid_id(client, auth_tokens, order_id):
    resp = await client.patch(
        f"/api/v1/orders/{order_id}/arrival",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_order_arrival_not_found(client, auth_tokens):
    resp = await client.patch(
        "/api/v1/orders/999/arrival",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404

async def test_order_arrival_invalid_state(client, auth_tokens):
    order = await create_order(client, auth_tokens)  # ISSUED, not PAID

    resp = await client.patch(
        f"/api/v1/orders/{order['id']}/arrival",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420

async def test_order_arrival_not_located(client, auth_tokens):
    order = await create_paid_order(client, auth_tokens, located=False)  # not located

    resp = await client.patch(
        f"/api/v1/orders/{order['id']}/arrival",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 500

async def test_order_arrival_no_auth(client):
    resp = await client.patch(
        "/api/v1/orders/1/arrival",
        follow_redirects=True,
    )
    assert resp.status_code == 401

async def test_order_arrival_forbidden_role(client, auth_tokens):
    resp = await client.patch(
        "/api/v1/orders/1/arrival",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403
