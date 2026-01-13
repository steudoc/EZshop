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
# HELPER FUNCTIONS
# ---------------------------

async def create_or_return_product(client, auth_tokens, barcode="614141007349", 
                        description="Test Product", price=2.99, 
                        position="1-A-1", quantity=0):
    """Helper function to create a product with given parameters."""
    product_data = {
        "description": description,
        "barcode": barcode,
        "price_per_unit": price,
        "quantity": 0,
        "position": position
    }
    get_resp = await client.get(
        "/api/v1/products/barcode/" + barcode,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )

    if get_resp.status_code == 200:
        return get_resp.json()
    
    resp = await client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert resp.status_code == 201
    product = resp.json()
    if quantity != 0:
        quant = await client.patch(
            f"/api/v1/products/{product['id']}/quantity",
            params={"quantity": quantity},
            headers=auth_header(auth_tokens, "admin"),
            follow_redirects=True
        )
        assert quant.status_code == 201

    res = await client.post(
        f'/api/v1/balance/set',
        params={'amount': 1000.0},
        follow_redirects=True,
        headers=auth_header(auth_tokens, "admin")
    )
    assert res.status_code == 201
    return product


async def create_sale(client, auth_tokens, role="cashier"):
    """Helper function to create a new sale."""
    resp = await client.post(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    return resp


async def create_paid_sale(client, auth_tokens, role="cashier", amount=1):
    """Helper function to create a paid sale."""
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]
    
    # Create product
    product = await create_or_return_product(client, auth_tokens, quantity=10)
    
    # Add product to sale
    add_resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": product["barcode"], "amount": amount},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    # Close sale
    close_resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    # Pay sale
    pay_resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 100.0},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert pay_resp.status_code == 200
    
    return sale_id


async def create_return(client, auth_tokens, sale_id, role="cashier"):
    """Helper function to create a return for a paid sale."""
    resp = await client.post(
        "/api/v1/returns",
        params={"sale_id": sale_id},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    return resp

# ---------------------------
# POST /returns - START RETURN TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_start_return_success_all_roles(client, auth_tokens, role):
    """Start return should succeed for all authorized roles."""
    # Create a paid sale
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    
    resp = await create_return(client, auth_tokens, sale_id, role)
    
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "OPEN"


async def test_start_multiple_returns(client, auth_tokens):
    """Should be able to start multiple returns."""
    sale_id1 = await create_paid_sale(client, auth_tokens, "cashier")
    sale_id2 = await create_paid_sale(client, auth_tokens, "cashier")
    
    return_ids = []
    
    for sale_id in [sale_id1, sale_id2]:
        resp = await create_return(client, auth_tokens, sale_id, "cashier")
        assert resp.status_code == 201
        return_ids.append(resp.json()["id"])
    
    # All returns should have unique IDs
    assert len(return_ids) == len(set(return_ids))

# ---------------------------
# POST /returns - START RETURN TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_sale_id", [-1, "abc", 1.5])
async def test_start_return_invalid_sale_id(client, auth_tokens, invalid_sale_id):
    """Starting return with invalid sale_id should return 400."""
    resp = await client.post(
        "/api/v1/returns",
        params={"sale_id": invalid_sale_id},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

# ---------------------------
# POST /returns - START RETURN TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("header_data, expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token_here"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_start_return_unauthorized(client, auth_tokens, header_data, expected_message):
    """Starting return without auth should return 401."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    
    resp = await client.post(
        "/api/v1/returns",
        params={"sale_id": sale_id},
        headers=header_data,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# POST /returns - START RETURN TESTS - 404 NOT FOUND
# ---------------------------

async def test_start_return_sale_not_found(client, auth_tokens):
    """Starting return for non-existent sale should return 404."""
    resp = await client.post(
        "/api/v1/returns",
        params={"sale_id": 99999},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404
    
# ---------------------------
# POST /returns - START RETURN TESTS - 420 INVALID STATE
# ---------------------------

async def test_start_return_sale_not_paid(client, auth_tokens):
    """Starting return for unpaid sale should return 420."""
    # Create sale but don't pay
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]
    
    resp = await client.post(
        "/api/v1/returns",
        params={"sale_id": sale_id},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

# ---------------------------
# GET /returns - LIST ALL RETURNS TESTS - SUCCESS CASES
# ---------------------------

async def test_list_returns_empty(client, auth_tokens):
    """Listing returns when none exist should return empty array."""
    resp = await client.get(
        "/api/v1/returns",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    returns = resp.json()
    assert isinstance(returns, list)
    assert len(returns) == 0


async def test_list_returns_with_one_return(client, auth_tokens):
    """Listing returns should return all created returns."""
    # Create a return
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    created_return = create_resp.json()
    
    # List returns
    list_resp = await client.get(
        "/api/v1/returns",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert list_resp.status_code == 200
    returns = list_resp.json()
    assert len(returns) == 1
    assert returns[0]["id"] == created_return["id"]
    assert returns[0]["status"] == "OPEN"


async def test_list_returns_with_multiple_returns(client, auth_tokens):
    """Listing should return all returns."""
    return_ids = []
    
    # Create multiple returns
    for _ in range(3):
        sale_id = await create_paid_sale(client, auth_tokens, "cashier")
        resp = await create_return(client, auth_tokens, sale_id, "cashier")
        assert resp.status_code == 201
        return_ids.append(resp.json()["id"])
    
    # List all returns
    list_resp = await client.get(
        "/api/v1/returns",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert list_resp.status_code == 200
    returns = list_resp.json()
    assert len(returns) == 3
    
    returned_ids = [r["id"] for r in returns]
    for return_id in return_ids:
        assert return_id in returned_ids


@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_list_returns_all_roles(client, auth_tokens, role):
    """All authorized roles can list returns."""
    resp = await client.get(
        "/api/v1/returns",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200

# ---------------------------
# GET /returns - LIST ALL RETURNS TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_list_returns_unauthorized(client, headers, expected_message):
    """Listing returns without auth should return 401."""
    resp = await client.get(
        "/api/v1/returns",
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# GET /returns/{return_id} - GET RETURN BY ID TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_get_return_by_id_success_all_roles(client, auth_tokens, role):
    """Get return by ID should succeed for all authorized roles."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == return_id
    assert data["sale_id"] == sale_id
    assert data["status"] == "OPEN"

# ---------------------------
# GET /returns/{return_id} - GET RETURN BY ID TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc", 1.5])
async def test_get_return_invalid_id(client, auth_tokens, invalid_id):
    """Getting return with invalid ID should return 400."""
    resp = await client.get(
        f"/api/v1/returns/{invalid_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

# ---------------------------
# GET /returns/{return_id} - GET RETURN BY ID TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_get_return_by_id_unauthorized(client, auth_tokens, headers, expected_message):
    """Getting return by ID without auth should return 401."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# GET /returns/{return_id} - GET RETURN BY ID TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("return_id", [99999, 1, 42])
async def test_get_return_by_id_not_found(client, auth_tokens, return_id):
    """Getting non-existent return should return 404."""
    resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# INTEGRATION & EDGE CASE TESTS
# ---------------------------

async def test_create_and_list_return_integration(client, auth_tokens):
    """Creating a return should make it appear in the list."""
    # List should be empty initially
    list_resp = await client.get(
        "/api/v1/returns",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert len(list_resp.json()) == 0
    
    # Create return
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    created_return = create_resp.json()
    
    # List should now contain the return
    list_resp = await client.get(
        "/api/v1/returns",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    returns = list_resp.json()
    assert len(returns) == 1
    assert returns[0]["id"] == created_return["id"]


async def test_create_get_by_id_integration(client, auth_tokens):
    """Created return should be retrievable by ID."""
    # Create return
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Get by ID
    get_resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert get_resp.status_code == 200
    
    # Data should match
    created_data = create_resp.json()
    fetched_data = get_resp.json()
    assert created_data["id"] == fetched_data["id"]
    assert created_data["sale_id"] == fetched_data["sale_id"]
    assert created_data["status"] == fetched_data["status"]

# ---------------------------
# DELETE /returns/{return_id} - DELETE RETURN TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_delete_return_success_all_roles(client, auth_tokens, role):
    """Delete return should succeed for all authorized roles."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = await client.delete(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 204
    
    # Verify it's deleted
    get_resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert get_resp.status_code == 404

# ---------------------------
# DELETE /returns/{return_id} - DELETE RETURN TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc", 1.5])
async def test_delete_return_invalid_id(client, auth_tokens, invalid_id):
    """Deleting return with invalid ID should return 400."""
    resp = await client.delete(
        f"/api/v1/returns/{invalid_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

# ---------------------------
# DELETE /returns/{return_id} - DELETE RETURN TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_delete_return_unauthorized(client, auth_tokens, headers, expected_message):
    """Deleting return without auth should return 401."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    resp = await client.delete(
        f"/api/v1/returns/{return_id}",
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# DELETE /returns/{return_id} - DELETE RETURN TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("return_id", [99999, 1, 42])
async def test_delete_return_not_found(client, auth_tokens, return_id):
    """Deleting non-existent return should return 404."""
    resp = await client.delete(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# DELETE /returns/{return_id} - DELETE RETURN TESTS - 420 INVALID STATE
# ---------------------------

async def test_delete_return_reimbursed(client, auth_tokens):
    """Deleting a reimbursed return should return 420."""
    # Create return
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product to return
    product = await create_or_return_product(client, auth_tokens, quantity=10)
    add_resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    # Close return
    close_resp = await client.patch(
        f"/api/v1/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    # Reimburse return
    reimburse_resp = await client.patch(
        f"/api/v1/returns/{return_id}/reimburse",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert reimburse_resp.status_code == 200
    
    # Try to delete
    resp = await client.delete(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

# ---------------------------
# POST /returns/{return_id}/items - ADD PRODUCT TO RETURN TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_add_product_to_return_success_all_roles(client, auth_tokens, role):
    """Add product to return should succeed for all authorized roles."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Get the product barcode from the sale
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    sale = sale_resp.json()
    barcode = sale["lines"][0]["product_barcode"]
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] == True

@pytest.mark.parametrize("amount", [1, 2, 5])
async def test_add_product_various_quantities(client, auth_tokens, amount):
    """Add product with various quantities."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier", amount=8)
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Get barcode
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": amount},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 201

# ---------------------------
# POST /returns/{return_id}/items - ADD PRODUCT TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_add_product_invalid_return_id(client, auth_tokens, invalid_id):
    """Adding product with invalid return ID should return 400."""
    resp = await client.post(
        f"/api/v1/returns/{invalid_id}/items",
        params={"barcode": "036000291452", "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

@pytest.mark.parametrize("invalid_amount", [0, -1, -10])
async def test_add_product_invalid_amount(client, auth_tokens, invalid_amount):
    """Adding product with invalid amount should return 400."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": invalid_amount},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

async def test_add_product_insufficient_quantity(client, auth_tokens):
    """Adding more products than sold should return 400."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 10},  # More than sold (1)
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

# ---------------------------
# POST /returns/{return_id}/items - ADD PRODUCT TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_add_product_unauthorized(client, auth_tokens, headers, expected_message):
    """Adding product without auth should return 401."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# POST /returns/{return_id}/items - ADD PRODUCT TESTS - 404 NOT FOUND
# ---------------------------

async def test_add_product_return_not_found(client, auth_tokens):
    """Adding product to non-existent return should return 404."""
    resp = await client.post(
        "/api/v1/returns/99999/items",
        params={"barcode": "036000291452", "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

async def test_add_product_not_in_sale(client, auth_tokens):
    """Adding product not in sale should return 400."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Create different product
    product = await create_or_return_product(client, auth_tokens, position="1-B-3", barcode="8435497287344", quantity=10)
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 404, 422)

# ---------------------------
# POST /returns/{return_id}/items - ADD PRODUCT TESTS - 420 INVALID STATE
# ---------------------------

async def test_add_product_closed_return(client, auth_tokens):
    """Adding product to closed return should return 420."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]

    #get product barcode
    product = await create_or_return_product(client, auth_tokens, quantity=10)

    # Add product to return
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp.status_code == 201
    
    # Close return
    close_resp = await client.patch(
        f"/api/v1/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    print("------------------------", sale_resp.json())
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

# ---------------------------
# DELETE /returns/{return_id}/items - REMOVE PRODUCT TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_remove_product_from_return_success_all_roles(client, auth_tokens, role):
    """Remove product from return should succeed for all authorized roles."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    # Add product first
    add_resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    # Remove product
    resp = await client.delete(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 202

# ---------------------------
# PATCH /returns/{return_id}/close - CLOSE RETURN TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_close_return_success_all_roles(client, auth_tokens, role):
    """Close return should succeed for all authorized roles."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    product = await create_or_return_product(client, auth_tokens, quantity=10)

    # Add product to return
    add_resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": product["barcode"], "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )

    resp = await client.patch(
        f"/api/v1/returns/{return_id}/close",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert resp.status_code == 200

    # Verify status changed
    get_resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert get_resp.json()["status"] == "CLOSED"

# ---------------------------
# PATCH /returns/{return_id}/reimburse - REIMBURSE RETURN TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager"])
async def test_reimburse_return_success_authorized_roles(client, auth_tokens, role):
    """Reimburse return should succeed for admin and manager."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    add_resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    # Close return
    close_resp = await client.patch(
        f"/api/v1/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    # Reimburse
    resp = await client.patch(
        f"/api/v1/returns/{return_id}/reimburse",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "refund_amount" in data
    
    # Verify status changed
    get_resp = await client.get(
        f"/api/v1/returns/{return_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert get_resp.json()["status"] == "REIMBURSED"

async def test_reimburse_return_cashier_unauthorized(client, auth_tokens):
    """Cashier should not be able to reimburse."""
    sale_id = await create_paid_sale(client, auth_tokens, "cashier")
    create_resp = await create_return(client, auth_tokens, sale_id, "cashier")
    assert create_resp.status_code == 201
    return_id = create_resp.json()["id"]
    
    # Add product and close
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    barcode = sale_resp.json()["lines"][0]["product_barcode"]
    
    add_resp = await client.post(
        f"/api/v1/returns/{return_id}/items",
        params={"barcode": barcode, "amount": 1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    close_resp = await client.patch(
        f"/api/v1/returns/{return_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    # Try reimburse as cashier
    resp = await client.patch(
        f"/api/v1/returns/{return_id}/reimburse",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 403