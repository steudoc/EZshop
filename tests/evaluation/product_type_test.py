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
# SAMPLE PRODUCT PAYLOADS
# ---------------------------

@pytest.fixture
def valid_product():
    return {
        "description": "Chocolate Bar",
        "barcode": "614141007349",
        "price_per_unit": 2.99,
        "note": "Imported from Belgium",
        "quantity": 0,
        "position": "1-A-3",
    }


@pytest.fixture
def minimal_product():
    return {
        "description": "Water Bottle",
        "barcode": "036000291452",
        "price_per_unit": 1.50,
    }


@pytest.fixture
def product_with_13_digit_barcode():
    return {
        "description": "Orange Juice",
        "barcode": "5901234123457",
        "price_per_unit": 3.99,
    }


@pytest.fixture
def product_with_14_digit_barcode():
    return {
        "description": "Apple Juice",
        "barcode": "10614141007343",
        "price_per_unit": 4.50,
    }

# ---------------------------
# CREATE PRODUCT — SUCCESS
# ---------------------------

async def test_create_product_success_as_admin(client, auth_tokens, valid_product):
    resp = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201


async def test_create_product_success_as_manager(client, auth_tokens, valid_product):
    resp = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "manager"),
        follow_redirects=True,
    )
    assert resp.status_code == 201


async def test_create_product_minimal_fields(client, auth_tokens, minimal_product):
    resp = await client.post(
        "/api/v1/products",
        json=minimal_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201


async def test_create_product_ignores_provided_id(client, auth_tokens, valid_product):
    payload = valid_product | {"id": 9999}
    resp = await client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    assert resp.json()["id"] != 9999


# ---------------------------
# CREATE PRODUCT — 400 / 422
# ---------------------------

@pytest.mark.parametrize("payload", [
    {"barcode": "036000291452", "price_per_unit": 2.99},
    {"description": "Test", "price_per_unit": 2.99},
    {"description": "Test", "barcode": "036000291452"},
    {"description": "Test", "barcode": "", "price_per_unit": 2.99},
    {"description": "Test", "barcode": "12345678901", "price_per_unit": 2.99},
    {"description": "Test", "barcode": "123456789012345", "price_per_unit": 2.99},
    {"description": "Test", "barcode": "12345678901A", "price_per_unit": 2.99},
    {"description": "Test", "barcode": "1234567890-2", "price_per_unit": 2.99},
    {"description": "Test", "barcode": "036000291452", "price_per_unit": 0},
    {"description": "Test", "barcode": "036000291452", "price_per_unit": -1},
    {"description": "Test", "barcode": "036000291452", "price_per_unit": "nope"},
])
async def test_create_product_bad_request(client, auth_tokens, payload):
    resp = await client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

# ---------------------------
# CREATE PRODUCT — AUTH
# ---------------------------

async def test_create_product_no_auth(client, valid_product):
    resp = await client.post(
        "/api/v1/products",
        json=valid_product,
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_create_product_invalid_token(client, valid_product):
    resp = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers={"Authorization": "Bearer invalid"},
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_create_product_forbidden_as_cashier(client, auth_tokens, valid_product):
    resp = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

@pytest.mark.parametrize("headers", [
    {"Authorization": "invalid"},
    {"Authorization": "Bearer"},
    {"Authorization": "Bearer "},
    {"Authorization": "Token abc"},
])
async def test_create_product_auth_header_edge_cases(client, valid_product, headers):
    resp = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=headers,
        follow_redirects=True,
    )
    assert resp.status_code == 401


# ---------------------------
# CREATE PRODUCT — CONFLICT
# ---------------------------

async def test_create_product_duplicate_barcode(client, auth_tokens, valid_product):
    resp1 = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp2.status_code == 409

# ---------------------------
# LIST PRODUCTS
# ---------------------------

async def test_list_products_empty(client, auth_tokens):
    resp = await client.get(
        "/api/v1/products",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_products_with_data(client, auth_tokens, valid_product):
    await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    resp = await client.get(
        "/api/v1/products",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_products_unauthorized(client):
    resp = await client.get(
        "/api/v1/products",
        follow_redirects=True,
    )
    assert resp.status_code == 401


@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_list_products_allowed_roles(client, auth_tokens, role):
    resp = await client.get(
        "/api/v1/products",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

async def test_list_products_response_shape(client, auth_tokens, valid_product):
    await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    resp = await client.get(
        "/api/v1/products",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200

    product = resp.json()[0]
    for field in ("id", "description", "barcode", "price_per_unit"):
        assert field in product

# ---------------------------
# GET PRODUCT BY ID
# --------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_get_product_by_id_allowed_roles(client, auth_tokens, valid_product, role):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.get(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 200

@pytest.mark.parametrize("product_id", [ -1, "abc"])
async def test_get_product_invalid_id(client, auth_tokens, product_id):
    resp = await client.get(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_get_product_not_found(client, auth_tokens):
    resp = await client.get(
        "/api/v1/products/999999",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404

@pytest.mark.parametrize("headers", [
    None,
    {"Authorization": "invalid"},
    {"Authorization": "Bearer"},
])
async def test_get_product_auth_edge_cases(client, headers):
    resp = await client.get(
        "/api/v1/products/1",
        headers=headers,
        follow_redirects=True,
    )
    assert resp.status_code == 401

# ---------------------------
# PUT PRODUCT 
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_update_product_success(client, auth_tokens, minimal_product, role):
    create = await client.post(
        "/api/v1/products",
        json=minimal_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={'barcode': '5901234123457',
            "price_per_unit": 9.99},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201


async def test_update_product_forbidden_roles(client, auth_tokens, valid_product):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={"price_per_unit": 5.0},
        headers=auth_header(auth_tokens, 'cashier'),
        follow_redirects=True,
    )
    assert resp.status_code == 403

@pytest.mark.parametrize("payload", [
    {"price_per_unit": -1},
    {"quantity": 0},
    {"barcode": "123"},
    {"barcode": "036000291452"},
])
async def test_update_product_invalid_payload(client, auth_tokens, valid_product, payload):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_update_product_not_found(client, auth_tokens):
    resp = await client.put(
        "/api/v1/products/999999",
        json={"barcode": '036000291452'},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404

async def test_update_product_barcode_conflict(client, auth_tokens):
    p1 = {"description": "A", "barcode": "036000291452", "price_per_unit": 1}
    p2 = {"description": "B", "barcode": "036000291452", "price_per_unit": 2}

    r1 = await client.post(
        "/api/v1/products", json=p1,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    r2 = await client.post(
        "/api/v1/products", json=p2,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    resp = await client.put(
        f"/api/v1/products/{r2.json()['id']}",
        json={"barcode": p1["barcode"]},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 409

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_delete_product_success(client, auth_tokens, valid_product, role):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 204

async def test_delete_product_invalid_id(client, auth_tokens):
    product_id = -1
    resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_delete_product_forbidden_role(client, auth_tokens):
    resp = await client.delete(
        "/api/v1/products/1",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

async def test_delete_product_not_found(client, auth_tokens):
    resp = await client.delete(
        "/api/v1/products/999999",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404

# ---------------------------
# GET PRODUCT BY BARCODE
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_get_product_by_barcode_success(client, auth_tokens, valid_product, role):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    barcode = create.json()["barcode"]

    resp = await client.get(
        f"/api/v1/products/barcode/{barcode}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 200

@pytest.mark.parametrize("barcode", [
    "",
    "123",
    "ABC123",
    "12345678901",      # too short
    "123456789012345",  # too long
])
async def test_get_product_by_barcode_invalid_format(client, auth_tokens, barcode):
    resp = await client.get(
        f"/api/v1/products/barcode/{barcode}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_get_product_by_barcode_not_found(client, auth_tokens):
    resp = await client.get(
        "/api/v1/products/barcode/036000291452",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404

async def test_get_product_by_barcode_forbidden_role(client, auth_tokens):
    resp = await client.get(
        "/api/v1/products/barcode/036000291452",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

@pytest.mark.parametrize("headers", [
    None,
    {"Authorization": "invalid"},
    {"Authorization": "Bearer"},
])
async def test_get_product_by_barcode_auth_edge_cases(client, headers):
    resp = await client.get(
        "/api/v1/products/barcode/036000291452",
        headers=headers,
        follow_redirects=True,
    )
    assert resp.status_code == 401

# ---------------------------
# SEARCH PRODUCTS BY DESCRIPTION
# ---------------------------

@pytest.mark.parametrize("query", ["milk", "choc"])
async def test_search_products_success(client, auth_tokens, valid_product, query):
    await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    params = {"query": query} if query is not None else {}

    resp = await client.get(
        "/api/v1/products/search",
        params=params,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_search_products_forbidden_role(client, auth_tokens):
    resp = await client.get(
        "/api/v1/products/search",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

@pytest.mark.parametrize("headers", [
    None,
    {"Authorization": "invalid"},
])
async def test_search_products_auth_edge_cases(client, headers):
    resp = await client.get(
        "/api/v1/products/search",
        headers=headers,
        follow_redirects=True,
    )
    assert resp.status_code == 401


async def test_update_position_success(client, auth_tokens, valid_product):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/products/{product_id}/position",
        params={"position": '2-B-1'},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201



async def test_update_position_success_reset(client, auth_tokens, valid_product):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/products/{product_id}/position",
        params={"position": ''},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    
    res = await client.get(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert res.json()["position"] == "" or res.json().get("position") is None        

@pytest.mark.parametrize("product_id, position", [
    (0, "1-A-1"),
    (-1, "1-A-1"),
    (1, "A-1-1"),
    (1, "1-1-A"),
    (1, "1-AA"),
])
async def test_update_position_bad_request(client, auth_tokens, product_id, position):
    resp = await client.patch(
        f"/api/v1/products/{product_id}/position",
        params={"position": position},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_update_position_forbidden_role(client, auth_tokens):
    resp = await client.patch(
        "/api/v1/products/1/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

async def test_update_position_conflict(client, auth_tokens):
    p1 = {"description": "A", "barcode": "036000291452", "price_per_unit": 1}
    p2 = {"description": "B", "barcode": "036000291452", "price_per_unit": 1}

    r1 = await client.post(
        "/api/v1/products", json=p1,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    r2 = await client.post(
        "/api/v1/products", json=p2,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    await client.patch(
        f"/api/v1/products/{r1.json()['id']}/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    resp = await client.patch(
        f"/api/v1/products/{r2.json()['id']}/position",
        params={"position": "1-A-1"},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 409

# ---------------------------
# UPDATE QUANTITY
# --------------------------

async def test_update_quantity_success(client, auth_tokens, valid_product):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/products/{product_id}/quantity",
        params={"quantity": 5},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201

async def test_update_quantity_bad_request_invalid_id(client, auth_tokens):
    resp = await client.patch(
        f"/api/v1/products/{-1}/quantity",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_update_quantity_bad_request_invalid_quantity(client, auth_tokens, valid_product):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]
    
    resp = await client.patch(
        f"/api/v1/products/{product_id}/quantity",
        params={"quantity": "A10"},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_update_quantity_bad_request_insufficient_quantity(client, auth_tokens, valid_product):
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]
    
    resp = await client.patch(
        f"/api/v1/products/{product_id}/quantity",
        params={"quantity": -10},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)       


async def test_update_quantity_forbidden_role(client, auth_tokens):
    resp = await client.patch(
        "/api/v1/products/1/quantity",
        params={"quantity": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True,
    )
    assert resp.status_code == 403

async def test_update_quantity_not_found(client, auth_tokens):
    resp = await client.patch(
        "/api/v1/products/999999/quantity",
        params={"quantity": 1},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


# ---------------------------
# 420 INVALID STATE - PRODUCT IN SALE
# ---------------------------

"""async def test_update_product_in_sale(client, auth_tokens, valid_product):
    #Cannot update or delete product involved in a sale
    # Create product
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    #set quantity to allow adding to sale
    await client.patch(
        f"/api/v1/products/{product_id}/quantity",
        params={"quantity": 10},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    # Create sale and add product
    sale_resp = await client.post(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    sale_id = sale_resp.json()["id"]

    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": valid_product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    # Try to update product
    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={"barcode": "614141007349", "price_per_unit": 5.0},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420

    # Try to delete product
    resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420
"""

# ---------------------------  
# 420 INVALID STATE - PRODUCT IN ORDER
# ---------------------------
"""
async def test_update_product_in_order(client, auth_tokens, valid_product):
    #Cannot update or delete product involved in an order
    # Create product
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    # Create order and add product
    order_resp = await client.post(
        "/api/v1/orders",
        headers=auth_header(auth_tokens, "admin"),
        json={'product_barcode': valid_product["barcode"],
              'quantity': 1,
              'price_per_unit': 1.0},
        follow_redirects=True,
    )
    assert order_resp.status_code == 201

    # Try to update product
    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={"barcode": "614141007349",
              "price_per_unit": 5.0},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420

    # Try to delete product
    resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420
"""
# ---------------------------  
# 420 INVALID STATE - PRODUCT IN RETURN
# ---------------------------

"""async def test_update_product_in_return(client, auth_tokens, valid_product):
    #Cannot update or delete product involved in a return.
    # Create product
    create = await client.post(
        "/api/v1/products",
        json=valid_product,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    product_id = create.json()["id"]

    #add quantity to allow sale
    quant = await client.patch(
        f"/api/v1/products/{product_id}/quantity",
        params={"quantity": 10},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert quant.status_code == 201

    #create a sale to allow return
    sale_resp = await client.post(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    add_resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": valid_product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    # Close sale
    close_resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    # Pay sale
    pay_resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 100.0},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert pay_resp.status_code == 200


    # Create return and add product
    return_resp = await client.post(
        "/api/v1/returns",
        params={"sale_id": sale_id},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert return_resp.status_code == 201
    return_id = return_resp.json()["id"]

    await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": valid_product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    # Try to update product
    resp = await client.put(
        f"/api/v1/products/{product_id}",
        json={'barcode': valid_product['barcode'],
              "price_per_unit": 5.0},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420

    # Try to delete product
    resp = await client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 420"""