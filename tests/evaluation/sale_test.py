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

async def create_product(client, auth_tokens, barcode="614141007349", 
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
    return product


async def create_sale(client, auth_tokens, role="cashier"):
    """Helper function to create a new sale."""
    resp = await client.post(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    return resp

# ---------------------------
# POST /sales - START SALE TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_start_sale_success_all_roles(client, auth_tokens, role):
    """All roles (Administrator, ShopManager, Cashier) should be able to start a new sale."""
    resp = await create_sale(client, auth_tokens, role)
    
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["status"] == "OPEN"
    assert data["discount_rate"] == 0.0


async def test_start_sale_default_values(client, auth_tokens):
    """New sale should have correct default values."""
    resp = await create_sale(client, auth_tokens, "cashier")
    
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "OPEN"
    assert data["discount_rate"] == 0.0


async def test_start_multiple_sales(client, auth_tokens):
    """Should be able to start multiple sales."""
    sale_ids = []
    
    for _ in range(3):
        resp = await create_sale(client, auth_tokens, "cashier")
        assert resp.status_code == 201
        sale_ids.append(resp.json()["id"])
    
    # All sales should have unique IDs
    assert len(sale_ids) == len(set(sale_ids))

# ---------------------------
# POST /sales - START SALE TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token_here"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_start_sale_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.post("/api/v1/sales", headers=headers,follow_redirects=True)
    
    assert resp.status_code == 401

# ---------------------------
# GET /sales - LIST ALL SALES TESTS - SUCCESS CASES
# ---------------------------

async def test_list_sales_empty(client, auth_tokens):
    """Listing sales when none exist should return empty array."""
    resp = await client.get(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    sales = resp.json()
    assert isinstance(sales, list)
    assert len(sales) == 0


async def test_list_sales_with_one_sale(client, auth_tokens):
    """Listing sales should return all created sales."""
    # Create a sale
    create_resp = await create_sale(client, auth_tokens, "cashier")
    assert create_resp.status_code == 201
    created_sale = create_resp.json()
    
    # List sales
    list_resp = await client.get(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert list_resp.status_code == 200
    sales = list_resp.json()
    assert len(sales) == 1
    assert sales[0]["id"] == created_sale["id"]
    assert sales[0]["status"] == "OPEN"


async def test_list_sales_with_multiple_sales(client, auth_tokens):
    """Listing should return all sales."""
    sale_ids = []
    
    # Create multiple sales
    for i in range(3):
        resp = await create_sale(client, auth_tokens, "cashier")
        assert resp.status_code == 201
        sale_ids.append(resp.json()["id"])
    
    # List all sales
    list_resp = await client.get(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert list_resp.status_code == 200
    sales = list_resp.json()
    assert len(sales) == 3
    
    returned_ids = [s["id"] for s in sales]
    for sale_id in sale_ids:
        assert sale_id in returned_ids


@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_list_sales_all_roles(client, auth_tokens, role):
    """All roles should be able to list sales."""
    resp = await client.get(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------
# GET /sales - LIST ALL SALES TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_list_sales_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.get("/api/v1/sales", headers=headers, follow_redirects=True)
    
    assert resp.status_code == 401

# ---------------------------
# GET /sales/{sale_id} - GET SALE BY ID TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_get_sale_by_id_success_all_roles(client, auth_tokens, role):
    """All roles should be able to get a sale by ID."""
    # Create sale
    create_resp = await create_sale(client, auth_tokens, "cashier")
    assert create_resp.status_code == 201
    sale_id = create_resp.json()["id"]
    
    # Get sale by ID
    resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sale_id
    assert data["status"] == "OPEN"
    assert "discount_rate" in data

# ---------------------------
# GET /sales/{sale_id} - GET SALE BY ID TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc", 1.5])
async def test_get_sale_invalid_id(client, auth_tokens, invalid_id):
    create_resp = await create_sale(client, auth_tokens, "cashier")
    assert create_resp.status_code == 201

    """Invalid sale IDs should return 400 or 422."""
    resp = await client.get(
        f"/api/v1/sales/{invalid_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

# ---------------------------
# GET /sales/{sale_id} - GET SALE BY ID TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_get_sale_by_id_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.get("/api/v1/sales/1", headers=headers, follow_redirects=True)
    
    assert resp.status_code == 401


# ---------------------------
# GET /sales/{sale_id} - GET SALE BY ID TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("sale_id", [99999, 1, 42])
async def test_get_sale_by_id_not_found(client, auth_tokens, sale_id):
    """Getting non-existent sale should return 404."""
    resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404


# ---------------------------
# INTEGRATION & EDGE CASE TESTS
# ---------------------------

async def test_create_and_list_sale_integration(client, auth_tokens):
    """Creating a sale should make it appear in the list."""
    # List should be empty initially
    list_resp = await client.get(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert len(list_resp.json()) == 0
    
    # Create sale
    create_resp = await create_sale(client, auth_tokens, "cashier")
    assert create_resp.status_code == 201
    created_sale = create_resp.json()
    
    # List should now contain the sale
    list_resp = await client.get(
        "/api/v1/sales",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    sales = list_resp.json()
    assert len(sales) == 1
    assert sales[0]["id"] == created_sale["id"]


async def test_create_get_by_id_integration(client, auth_tokens):
    """Created sale should be retrievable by ID."""
    # Create sale
    create_resp = await create_sale(client, auth_tokens, "cashier")
    assert create_resp.status_code == 201
    sale_id = create_resp.json()["id"]
    
    # Get by ID
    get_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert get_resp.status_code == 200
    
    # Data should match
    created_data = create_resp.json()
    fetched_data = get_resp.json()
    assert created_data["id"] == fetched_data["id"]
    assert created_data["status"] == fetched_data["status"]
    assert created_data["discount_rate"] == fetched_data["discount_rate"]

# ---------------------------
# DELETE /sales/{sale_id} - DELETE SALE TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_delete_sale_success_all_roles(client, auth_tokens, role):
    """All roles should be able to delete an OPEN sale."""
    # Create sale
    create_resp = await create_sale(client, auth_tokens, "cashier")
    assert create_resp.status_code == 201
    sale_id = create_resp.json()["id"]

    
    # Delete sale
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 204
    
    # Verify sale is deleted
    get_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert get_resp.status_code == 404


# ---------------------------
# DELETE /sales/{sale_id} - DELETE SALE TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [ -1, "abc", 1.5])
async def test_delete_sale_invalid_id(client, auth_tokens, invalid_id):
    """Invalid sale IDs should return 400 or 422."""
    resp = await client.delete(
        f"/api/v1/sales/{invalid_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code in (400, 422)


# ---------------------------
# DELETE /sales/{sale_id} - DELETE SALE TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_delete_sale_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.delete("/api/v1/sales/1", headers=headers)
    
    assert resp.status_code == 401


# ---------------------------
# DELETE /sales/{sale_id} - DELETE SALE TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("sale_id", [99999, 1, 42])
async def test_delete_sale_not_found(client, auth_tokens, sale_id):
    """Deleting non-existent sale should return 404."""
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# DELETE /sales/{sale_id} - DELETE SALE TESTS - 420 INVALID STATE
# ---------------------------
    
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_add_item_closed_sale(client, auth_tokens, role):
    """Applying discount to closed sale should return 420."""
    prod = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert sale_resp.status_code == 201
    
    # Mark sale as pending
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        params={"status": "pending"},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )

    # Try to delete paid sale
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_add_item_paid_sale(client, auth_tokens, role):
    """Applying discount to paid sale should return 420."""
    prod = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert sale_resp.status_code == 201
    
    # Mark sale as pending
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        params={"status": "pending"},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )

    await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        headers=auth_header(auth_tokens, role),
        params={'cash_amount': 100.0},
        follow_redirects=True
    )

    # Try to delete paid sale
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420


# ---------------------------
# POST /sales/{sale_id}/items - ADD PRODUCT TO SALE TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_add_product_to_sale_success_all_roles(client, auth_tokens, role):
    """All roles should be able to add products to a sale."""
    # Create product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=100)
    
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 201

@pytest.mark.parametrize("amount", [1, 5, 10, 25, 50])
async def test_add_product_various_quantities(client, auth_tokens, amount):
    """Should be able to add products with various quantities."""
    # Create product with sufficient quantity
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=100)
    
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": amount},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 201
    
    # Verify quantity deducted
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 100 - amount


async def test_add_product_deducts_from_inventory(client, auth_tokens):
    """Adding product to sale should deduct from inventory."""
    # Create product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=100)

    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 20},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp.status_code == 201
    
    # Check inventory
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 80


async def test_add_multiple_products_to_sale(client, auth_tokens):
    """Should be able to add multiple different products to a sale."""
    # Create multiple products
    product1 = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    product2 = await create_product(client, auth_tokens, barcode="036000291452", position="2-B-2", quantity=30)
    
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add first product
    resp1 = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp1.status_code == 201
    
    # Add second product
    resp2 = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "036000291452", "amount": 3},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp2.status_code == 201
    
    # Verify sale has both products
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    sale = sale_resp.json()
    assert len(sale["lines"]) == 2


async def test_add_same_product_multiple_times(client, auth_tokens):
    """Adding the same product multiple times should accumulate quantity."""
    # Create product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=100)
    
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product twice
    resp1 = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp1.status_code == 201
    
    resp2 = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 3},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp2.status_code == 201
    
    # Verify total quantity deducted
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 92


# ---------------------------
# POST /sales/{sale_id}/items - ADD PRODUCT TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_add_product_invalid_sale_id(client, auth_tokens, invalid_id):
    """Invalid sale ID should return 400 or 422."""
    resp = await client.post(
        f"/api/v1/sales/{invalid_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


@pytest.mark.parametrize("invalid_amount", [0, -1, -10])
async def test_add_product_invalid_amount(client, auth_tokens, invalid_amount):
    """Amount must be positive."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)

    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": invalid_amount},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


async def test_add_product_insufficient_stock(client, auth_tokens):
    """Adding more than available quantity should fail."""
    # Create product with limited quantity
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=5)

    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Try to add more than available
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


async def test_add_product_missing_barcode(client, auth_tokens):
    """Missing barcode parameter should fail."""
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


async def test_add_product_missing_amount(client, auth_tokens):
    """Missing amount parameter should fail."""
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349"},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


# ---------------------------
# POST /sales/{sale_id}/items - ADD PRODUCT TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_add_product_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.post(
        "/api/v1/sales/1/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# POST /sales/{sale_id}/items - ADD PRODUCT TESTS - 404 NOT FOUND
# ---------------------------

async def test_add_product_sale_not_found(client, auth_tokens):
    """Adding product to non-existent sale should return 404."""
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    
    resp = await client.post(
        "/api/v1/sales/99999/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

async def test_add_product_not_found(client, auth_tokens):
    """Adding non-existent product should return 404."""
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "8435497287344", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# DELETE /sales/{sale_id}/items - REMOVE PRODUCT TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_remove_product_from_sale_success_all_roles(client, auth_tokens, role):
    """All roles should be able to remove products from a sale."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")

    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Remove product
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 202

async def test_remove_product_restores_inventory(client, auth_tokens):
    """Removing product from sale should restore inventory."""
    # Create product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=100)
    
    # Create sale and add product
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 20},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Verify quantity decreased
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 80
    
    # Remove product
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp.status_code == 202
    
    # Verify quantity restored
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 90


async def test_remove_entire_product_quantity(client, auth_tokens):
    """Removing all quantity should remove product line from sale."""
    # Create product and sale
    await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Remove all quantity
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp.status_code == 202
    
    # Verify sale has no lines
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    sale = sale_resp.json()
    assert len(sale["lines"]) == 0


@pytest.mark.parametrize("add_amount,remove_amount", [
    (10, 5),
    (20, 10),
    (15, 15),
    (100, 50),
])
async def test_remove_product_various_quantities(client, auth_tokens, add_amount, remove_amount):
    """Should be able to remove various quantities."""
    # Create product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=200)
    
    # Create sale and add product
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": add_amount},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Remove product
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": remove_amount},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 202
    # Verify quantity restored
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 200 - (add_amount - remove_amount)


# ---------------------------
# DELETE /sales/{sale_id}/items - REMOVE PRODUCT TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_remove_product_invalid_sale_id(client, auth_tokens, invalid_id):
    """Invalid sale ID should return 400 or 422."""
    resp = await client.delete(
        f"/api/v1/sales/{invalid_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


@pytest.mark.parametrize("invalid_amount", [0, -1, -10])
async def test_remove_product_invalid_amount(client, auth_tokens, invalid_amount):
    """Amount must be positive."""
    # Create product and sale with item
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Try to remove with invalid amount
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": invalid_amount},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code in (400, 422)


async def test_remove_more_than_in_sale(client, auth_tokens):
    """Removing more than what's in sale should fail."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add 5 items
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Try to remove 10
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


# ---------------------------
# DELETE /sales/{sale_id}/items - REMOVE PRODUCT TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_remove_product_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.delete(
        "/api/v1/sales/1/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401


# ---------------------------
# DELETE /sales/{sale_id}/items - REMOVE PRODUCT TESTS - 404 NOT FOUND
# ---------------------------

async def test_remove_product_sale_not_found(client, auth_tokens):
    """Removing product from non-existent sale should return 404."""
    resp = await client.delete(
        "/api/v1/sales/99999/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

async def test_remove_product_not_in_sale(client, auth_tokens):
    """Removing product that's not in sale should return 404."""
    # Create product and sale (but don't add product to sale)
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# DELETE /sales/{sale_id}/items - REMOVE PRODUCT TESTS - 420 SALE FINALIZED
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_delete_item_closed_sale(client, auth_tokens, role):
    """Applying discount to closed sale should return 420."""
    prod = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert sale_resp.status_code == 201
    
    # Mark sale as pending
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        params={"status": "pending"},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )

    # Try to delete product from paid sale
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_delete_item_paid_sale(client, auth_tokens, role):
    """Applying discount to paid sale should return 420."""
    prod = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert sale_resp.status_code == 201
    
    # Mark sale as pending
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        params={"status": "pending"},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )

    await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        headers=auth_header(auth_tokens, role),
        params={'cash_amount': 100.0},
        follow_redirects=True
    )

    # Try to delete product from paid sale
    resp = await client.delete(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420
# ---------------------------
# PATCH /sales/{sale_id}/discount - APPLY SALE DISCOUNT TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_apply_sale_discount_success_all_roles(client, auth_tokens, role):
    """All roles should be able to apply discount to sale."""
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Apply discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    
    # Verify discount applied
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert sale_resp.json()["discount_rate"] == 0.1


@pytest.mark.parametrize("discount_rate", [ 0.05, 0.1, 0.25, 0.5, 0.75, 0.99])
async def test_apply_sale_discount_various_rates(client, auth_tokens, discount_rate):
    """Should be able to apply various valid discount rates."""
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Apply discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": discount_rate},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    
    # Verify discount
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert abs(sale_resp.json()["discount_rate"] - discount_rate) < 0.001

async def test_apply_sale_discount_overwrite_existing(client, auth_tokens):
    """Applying discount should overwrite existing discount."""
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Apply first discount
    resp1 = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp1.status_code == 200
    
    # Apply second discount
    resp2 = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.2},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp2.status_code == 200
    
    # Verify second discount is applied
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert sale_resp.json()["discount_rate"] == 0.2


# ---------------------------
# PATCH /sales/{sale_id}/discount - APPLY SALE DISCOUNT TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_apply_sale_discount_invalid_id(client, auth_tokens, invalid_id):
    """Invalid sale ID should return 400 or 422."""
    resp = await client.patch(
        f"/api/v1/sales/{invalid_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


@pytest.mark.parametrize("invalid_rate", [-0.1, 1.0, 1.5, 2.0, -1.0])
async def test_apply_sale_discount_invalid_rate(client, auth_tokens, invalid_rate):
    """Invalid discount rate should return 400 or 422."""
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Try to apply invalid discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": invalid_rate},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

async def test_apply_sale_discount_missing_rate(client, auth_tokens):
    """Missing discount_rate parameter should fail."""
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


# ---------------------------
# PATCH /sales/{sale_id}/discount - APPLY SALE DISCOUNT TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_apply_sale_discount_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.patch(
        "/api/v1/sales/1/discount",
        params={"discount_rate": 0.1},
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401


# ---------------------------
# PATCH /sales/{sale_id}/discount - APPLY SALE DISCOUNT TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("sale_id", [99999, 1])
async def test_apply_sale_discount_not_found(client, auth_tokens, sale_id):
    """Applying discount to non-existent sale should return 404."""
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# PATCH /sales/{sale_id}/discount - APPLY SALE DISCOUNT TESTS - 420 Non open Sale
# ---------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_apply_sale_discount_pending_sale(client, auth_tokens, role):
    """Applying discount to pending sale should return 420."""
    prod = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert sale_resp.status_code == 201
    
    # Mark sale as pending
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        params={"status": "pending"},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    # Try to apply discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_apply_sale_discount_paid_sale(client, auth_tokens, role):
    """Applying discount to paid sale should return 420."""
    prod = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    # Create sale
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]

    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    assert sale_resp.status_code == 201
    
    # Mark sale as pending
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        params={"status": "pending"},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )

    await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        headers=auth_header(auth_tokens, role),
        params={'cash_amount': 100.0},
        follow_redirects=True
    )

    # Try to apply discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420


# ---------------------------
# PATCH /sales/{sale_id}/items/{barcode}/discount - PRODUCT DISCOUNT TESTS - SUCCESS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_apply_product_discount_success_all_roles(client, auth_tokens, role):
    """All roles should be able to apply discount to product in sale."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Apply product discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": 0.15},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200


@pytest.mark.parametrize("discount_rate", [ 0.1, 0.2, 0.5, 0.99])
async def test_apply_product_discount_various_rates(client, auth_tokens, discount_rate):
    """Should be able to apply various valid discount rates to products."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Apply discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": discount_rate},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 200


async def test_apply_discount_to_multiple_products(client, auth_tokens):
    """Should be able to apply different discounts to different products."""
    # Create products and sale
    product1 = await create_product(client, auth_tokens, barcode="614141007349", position='1-A-1', quantity=50)
    product2 = await create_product(client, auth_tokens, barcode="036000291452", position='1-A-3', quantity=30)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add products
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "036000291452", "amount": 3},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Apply different discounts
    resp1 = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp1.status_code == 200
    
    resp2 = await client.patch(
        f"/api/v1/sales/{sale_id}/items/036000291452/discount",
        params={"discount_rate": 0.2},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert resp2.status_code == 200

# ---------------------------
# PATCH /sales/{sale_id}/items/{barcode}/discount - PRODUCT DISCOUNT TESTS - 400
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_apply_product_discount_invalid_sale_id(client, auth_tokens, invalid_id):
    """Invalid sale ID should return 400 or 422."""
    resp = await client.patch(
        f"/api/v1/sales/{invalid_id}/items/614141007349/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


@pytest.mark.parametrize("invalid_rate", [-0.1, 1.0, 1.5, -1.0])
async def test_apply_product_discount_invalid_rate(client, auth_tokens, invalid_rate):
    """Invalid discount rate should return 400 or 422."""
    # Create product and sale with item
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Try invalid discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": invalid_rate},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


# ---------------------------
# PATCH /sales/{sale_id}/items/{barcode}/discount - PRODUCT DISCOUNT TESTS - 401
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_apply_product_discount_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.patch(
        "/api/v1/sales/1/items/614141007349/discount",
        params={"discount_rate": 0.1},
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401

# ---------------------------
# PATCH /sales/{sale_id}/items/{barcode}/discount - PRODUCT DISCOUNT TESTS - 404
# ---------------------------

async def test_apply_product_discount_sale_not_found(client, auth_tokens):
    """Applying discount to product in non-existent sale should return 404."""
    resp = await client.patch(
        "/api/v1/sales/99999/items/614141007349/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404


async def test_apply_product_discount_product_not_in_sale(client, auth_tokens):
    """Applying discount to product not in sale should return 404."""
    # Create product and sale (don't add product)
    await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# PATCH /sales/{sale_id}/items/{barcode}/discount - PRODUCT DISCOUNT TO A CLOSED SALE - 420
# ---------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_apply_product_discount_to_not_open_sale(client, auth_tokens, role):
    """Applying discount to product in a not OPEN sale should return 420."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    # Close the sale
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    # Try to apply product discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": 0.15},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

# ---------------------------
# PATCH /sales/{sale_id}/items/{barcode}/discount - PRODUCT DISCOUNT TO A PAID SALE - 420
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_apply_product_discount_to_paid_sale(client, auth_tokens, role):
    """Applying discount to product in a not OPEN sale should return 420."""
    # Create product and sale
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    # Close the sale
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )

    # Simulate payment to set sale to PAID
    await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        headers=auth_header(auth_tokens, role),
        params={'cash_amount' : 100.0},
        follow_redirects=True
    )
    
    # Try to apply product discount
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/items/614141007349/discount",
        params={"discount_rate": 0.15},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

# ---------------------------
# PATCH /sales/{sale_id}/close - CLOSE SALE TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_close_sale_success_all_roles(client, auth_tokens, role):
    """All roles should be able to close a sale."""
    # Create sale with product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Close sale
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    
    # Verify status changed to PENDING
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert sale_resp.json()["status"] == "PENDING"


async def test_close_empty_sale_deletes_it(client, auth_tokens):
    """Closing an empty sale should delete it from database."""
    # Create empty sale
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Close empty sale
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    
    # Verify sale is deleted
    get_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert get_resp.status_code == 404


async def test_close_sale_sets_closed_at_timestamp(client, auth_tokens):
    """Closing sale should set closed_at timestamp."""
    # Create sale with product
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Close sale
    close_resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert close_resp.status_code == 200
    
    # Verify closed_at is set
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    sale = sale_resp.json()
    assert sale["closed_at"] is not None


# ---------------------------
# PATCH /sales/{sale_id}/close - CLOSE SALE TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_close_sale_invalid_id(client, auth_tokens, invalid_id):
    """Invalid sale ID should return 400 or 422."""
    resp = await client.patch(
        f"/api/v1/sales/{invalid_id}/close",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)


# ---------------------------
# PATCH /sales/{sale_id}/close - CLOSE SALE TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_close_sale_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.patch(
        "/api/v1/sales/1/close",
        headers=headers,
        follow_redirects=True
    )
    
    assert resp.status_code == 401


# ---------------------------
# PATCH /sales/{sale_id}/close - CLOSE SALE TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("sale_id", [99999, 1])
async def test_close_sale_not_found(client, auth_tokens, sale_id):
    """Closing non-existent sale should return 404."""
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------
# PATCH /sales/{sale_id}/close - CLOSE A PAID SALE - 420 
# ---------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_close_paid_sale_fails(client, auth_tokens, role):
    """Closing an already paid sale should return 420."""
    # Create, add product, close, and pay for sale
    product = await create_product(client, auth_tokens, barcode="614141007349", price=10.0, quantity=50)
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 2},
        headers=auth_header(auth_tokens, role)
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role)
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 25.0},
        headers=auth_header(auth_tokens, role)
    )
    
    # Attempt to close again
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role)
    )
    
    assert resp.status_code == 420


# ---------------------------
# PATCH /sales/{sale_id}/pay - PAY SALE TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_pay_sale_success_all_roles(client, auth_tokens, role):
    """All roles should be able to pay for a sale."""
    # Create, add product, and close sale
    product = await create_product(client, auth_tokens, barcode="614141007349", price=10.0, quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 2},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Pay for sale
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 25.0},
        headers=auth_header(auth_tokens, role)
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "change" in data
    assert data["change"] == 5.0  # 25 - 20 = 5
    
    # Verify status changed to PAID
    sale_resp = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert sale_resp.json()["status"] == "PAID"


@pytest.mark.parametrize("price,quantity,cash,expected_change", [
    (10.0, 1, 10.0, 0.0),
    (10.0, 1, 15.0, 5.0),
    (10.0, 2, 25.0, 5.0),
    (5.5, 3, 20.0, 3.5),
    (2.99, 5, 20.0, 5.05),
])
async def test_pay_sale_change_calculation(client, auth_tokens, price, quantity, cash, expected_change):
    """Should calculate correct change for various scenarios."""
    # Create sale with product
    product = await create_product(client, auth_tokens, barcode="614141007349", price=price, quantity=100)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": quantity},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Pay
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": cash},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 200
    assert abs(resp.json()["change"] - expected_change) < 0.01


async def test_pay_sale_with_discount(client, auth_tokens):
    """Payment should account for sale discount."""
    # Create sale with product and discount
    product = await create_product(client, auth_tokens, barcode="614141007349", price=100.0, quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 1},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Apply 10% discount
    await client.patch(
        f"/api/v1/sales/{sale_id}/discount",
        params={"discount_rate": 0.1},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Pay - should be 90 (100 - 10%)
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 100.0},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 200
    assert abs(resp.json()["change"] - 10.0) < 0.01


# ---------------------------
# PATCH /sales/{sale_id}/pay - PAY SALE TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc"])
async def test_pay_sale_invalid_id(client, auth_tokens, invalid_id):
    """Invalid sale ID should return 400 or 422."""
    resp = await client.patch(
        f"/api/v1/sales/{invalid_id}/pay",
        params={"cash_amount": 20.0},
        headers=auth_header(auth_tokens, "admin")
    )
    
    assert resp.status_code in (400, 422)


@pytest.mark.parametrize("invalid_cash", [0.0, -10.0, -1.0])
async def test_pay_sale_invalid_cash_amount(client, auth_tokens, invalid_cash):
    """Invalid cash amount should return 400 or 422."""
    # Create and close sale
    product = await create_product(client, auth_tokens, barcode="614141007349", price=10.0, quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 1},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Try invalid cash
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": invalid_cash},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code in (400, 422)


async def test_pay_sale_insufficient_cash(client, auth_tokens):
    """Paying with insufficient cash should fail."""
    # Create sale total = 20
    product = await create_product(client, auth_tokens, barcode="614141007349", price=10.0, quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 2},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Try to pay with only 15
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 15.0},
        headers=auth_header(auth_tokens, "cashier")
    )

    assert not resp.status_code == 200


# ---------------------------
# PATCH /sales/{sale_id}/pay - PAY SALE TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
])
async def test_pay_sale_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.patch(
        "/api/v1/sales/1/pay",
        params={"cash_amount": 20.0},
        headers=headers
    )
    
    assert resp.status_code == 401


# ---------------------------
# PATCH /sales/{sale_id}/pay - PAY SALE TESTS - 404 NOT FOUND
# ---------------------------

@pytest.mark.parametrize("sale_id", [99999, 1])
async def test_pay_sale_not_found(client, auth_tokens, sale_id):
    """Paying for non-existent sale should return 404."""
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 20.0},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    assert resp.status_code == 404

# ---------------------------
# PATCH /sales/{sale_id}/pay - PAY SALE TESTS - 420 PAYING AN UNCLOSED SALE
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_pay_uncclosed_sale(client, auth_tokens, role):
    """Paying for an unclosed sale should return 420."""
    # Create sale with product
    product = await create_product(client, auth_tokens, barcode="614141007349", price=10.0, quantity=50)
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 2},
        headers=auth_header(auth_tokens, "cashier")
    )
    
    # Try to pay without closing
    resp = await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 25.0},
        headers=auth_header(auth_tokens, role)
    )
    
    assert resp.status_code == 420

# ---------------------------
# GET /sales/{sale_id}/points - COMPUTE POINTS TESTS - SUCCESS CASES
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_compute_points_success_all_roles(client, auth_tokens, role):
    """All roles should be able to compute points for a paid sale."""
    # Create product, sale, add product, close, pay
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, role)
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/pay",
        params={"cash_amount": 20.0},
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    # Compute points
    resp = await client.get(
        f"/api/v1/sales/{sale_id}/points",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "points" in data
    assert isinstance(data["points"], int)
    assert data["points"] >= 0

# ---------------------------  
# GET /sales/{sale_id}/points - COMPUTE POINTS TESTS - 400 BAD REQUEST
# ---------------------------

@pytest.mark.parametrize("invalid_id", [-1, "abc", 1.5])
async def test_compute_points_invalid_id(client, auth_tokens, invalid_id):
    """Invalid sale IDs should return 400 or 422."""
    resp = await client.get(
        f"/api/v1/sales/{invalid_id}/points",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code in (400, 422)

# ---------------------------  
# GET /sales/{sale_id}/points - COMPUTE POINTS TESTS - 401 UNAUTHORIZED
# ---------------------------

@pytest.mark.parametrize("headers,expected_message", [
    ({}, "Authorization header missing"),
    ({"Authorization": "Bearer invalid_token"}, None),
    ({"Authorization": "InvalidFormat token"}, None),
    ({"Authorization": "Bearer "}, None),
])
async def test_compute_points_unauthorized(client, headers, expected_message):
    """Request without valid authentication should return 401."""
    resp = await client.get("/api/v1/sales/1/points", headers=headers, follow_redirects=True)
    
    assert resp.status_code == 401

# ---------------------------  
# GET /sales/{sale_id}/points - COMPUTE POINTS TESTS - 404 NOT FOUND
# ---------------------------

async def test_compute_points_sale_not_found(client, auth_tokens):
    """Computing points for non-existent sale should return 404."""
    resp = await client.get(
        "/api/v1/sales/99999/points",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 404

# ---------------------------  
# GET /sales/{sale_id}/points - COMPUTE POINTS TESTS - 420 SALE NOT PAID
# ---------------------------

async def test_compute_points_sale_not_paid(client, auth_tokens):
    """Computing points for unpaid sale should return 420."""
    # Create sale with product and close but don't pay
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    await client.patch(
        f"/api/v1/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Try to compute points without paying
    resp = await client.get(
        f"/api/v1/sales/{sale_id}/points",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

async def test_compute_points_sale_not_closed(client, auth_tokens):
    """Computing points for open sale should return 420."""
    # Create sale with product and close but don't pay
    product = await create_product(client, auth_tokens, barcode="614141007349", quantity=50)
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    await client.post(
        f"/api/v1/sales/{sale_id}/items",
        params={"barcode": "614141007349", "amount": 5},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    
    # Try to compute points without paying
    resp = await client.get(
        f"/api/v1/sales/{sale_id}/points",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    
    assert resp.status_code == 420

# ---------------------------
async def test_delete_sale_restores_product_quantity(client, auth_tokens):
    """Deleting a sale should restore product quantities to inventory."""
    # Create product with quantity
    product = await create_product(
        client, auth_tokens, 
        barcode="614141007349",
        quantity=100
    )
    
    # Create sale and add product
    sale_resp = await create_sale(client, auth_tokens, "cashier")
    sale_id = sale_resp.json()["id"]
    
    # Add product to sale
    add_resp = await client.post(
        f"/api/v1/sales/{sale_id}/items?barcode=614141007349&amount=10",
        #params={"barcode": "614141007349", "amount": 10},
        headers=auth_header(auth_tokens, "cashier"),
        follow_redirects=True
    )
    assert add_resp.status_code == 201
    
    # Check product quantity decreased
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True
    )
    assert product_resp.json()["quantity"] == 90
    
    # Delete sale
    delete_resp = await client.delete(
        f"/api/v1/sales/{sale_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert delete_resp.status_code == 204
    
    # Check product quantity restored
    product_resp = await client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert product_resp.json()["quantity"] == 100