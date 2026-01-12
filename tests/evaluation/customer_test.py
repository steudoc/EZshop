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
# SAMPLE PAYLOADS
# ---------------------------

@pytest.fixture
def customer_sample():
    """Sample customer payload for testing."""
    return {
        "name": "Mario Rossi"
    }


@pytest.fixture
def customer_with_card_sample():
    """Sample customer with card payload."""
    return {
        "name": "Luigi Bianchi",
        "card": {
            "card_id": "0000000123",
            "points": 50
        }
    }


@pytest.fixture
def customer_update_sample():
    """Sample customer update payload."""
    return {
        "name": "Mario Rossi Updated"
    }


#---------------------------
# CUSTOMER CARD TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_create_customer_card_success(client, auth_tokens, role):
    """All roles should be able to create a new customer card."""
    resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    card = resp.json()
    assert "card_id" in card
    assert card["points"] == 0


async def test_create_customer_card_unauthenticated(client):
    """Creating a card without authentication should return 401."""
    resp = await client.post("/api/v1/customers/cards", follow_redirects=True)
    assert resp.status_code == 401


@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_attach_card_to_customer_success(client, auth_tokens, customer_sample, role):
    """All roles should be able to attach a card to a customer."""
    # Create customer
    cust_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    customer_id = cust_resp.json()["id"]

    # Create card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

# ---------------------------
# CREATE CUSTOMER TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_create_customer_success(client, auth_tokens, customer_sample, role):
    """All roles should be able to create a new customer."""
    resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == customer_sample["name"]
    assert "id" in data
    assert data["id"] > 0


@pytest.mark.parametrize("payload", [
    {},  # missing name
    {"name": ""},  # empty name
])
async def test_create_customer_bad_request(client, auth_tokens, payload):
    """Creating a customer with invalid payload should fail."""
    resp = await client.post(
        "/api/v1/customers",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)


async def test_create_customer_unauthenticated(client, customer_sample):
    """Creating a customer without authentication should return 401."""
    resp = await client.post("/api/v1/customers", json=customer_sample, follow_redirects=True)
    assert resp.status_code == 401


async def test_create_customer_with_invalid_card(client, auth_tokens):
    """Creating a customer with non-existent card should fail."""
    payload = {
        "name": "Test Customer",
        "card": {
            "card_id": "9999999999",
            "points": 0
        }
    }
    resp = await client.post(
        "/api/v1/customers",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert not resp.status_code == 201  # Should fail


# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_list_customers_success(client, auth_tokens, role):
    """All roles should be able to list all customers."""
    resp = await client.get("/api/v1/customers", headers=auth_header(auth_tokens, role), follow_redirects=True)
    assert resp.status_code == 200
    customers = resp.json()
    assert isinstance(customers, list)


async def test_list_customers_unauthenticated(client):
    """Listing customers without authentication should return 401."""
    resp = await client.get("/api/v1/customers", follow_redirects=True)
    assert resp.status_code == 401


async def test_list_customers_includes_created(client, auth_tokens, customer_sample):
    """List should include created customers."""
    # Create a customer
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert create_resp.status_code == 201
    created_customer = create_resp.json()

    # List customers
    list_resp = await client.get("/api/v1/customers", headers=auth_header(auth_tokens, "admin"), follow_redirects=True)
    assert list_resp.status_code == 200
    customers = list_resp.json()
    customer_names = [c["name"] for c in customers]
    assert customer_sample["name"] in customer_names


# ---------------------------
# GET CUSTOMER BY ID TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_get_customer_by_id_success(client, auth_tokens, customer_sample, role):
    """All roles should be able to get a customer by ID."""
    # Create a customer first
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert create_resp.status_code == 201
    customer_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/customers/{customer_id}", headers=auth_header(auth_tokens, role), follow_redirects=True)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == customer_id
    assert data["name"] == customer_sample["name"]


async def test_get_customer_not_found(client, auth_tokens):
    """Getting a non-existent customer should return 404."""
    resp = await client.get("/api/v1/customers/99999", headers=auth_header(auth_tokens, "admin"), follow_redirects=True)
    assert resp.status_code == 404


@pytest.mark.parametrize("customer_id", [-1, "abc"])
async def test_get_customer_invalid_id(client, auth_tokens, customer_id):
    """Getting a customer with invalid ID should return 400."""
    resp = await client.get(f"/api/v1/customers/{customer_id}", headers=auth_header(auth_tokens, "admin"), follow_redirects=True)
    assert resp.status_code in (400, 422)


async def test_get_customer_unauthenticated(client):
    """Getting a customer without authentication should return 401."""
    resp = await client.get("/api/v1/customers/1", follow_redirects=True)
    assert resp.status_code == 401


# ---------------------------
# UPDATE CUSTOMER TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_update_customer_success(client, auth_tokens, customer_sample, customer_update_sample, role):
    """All roles should be able to update a customer."""
    # Create a customer
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert create_resp.status_code == 201
    customer_id = create_resp.json()["id"]

    # Update the customer
    resp = await client.put(
        f"/api/v1/customers/{customer_id}",
        json=customer_update_sample,
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    updated_customer = resp.json()
    assert updated_customer["name"] == customer_update_sample["name"]
    assert updated_customer["id"] == customer_id


async def test_update_customer_not_found(client, auth_tokens, customer_update_sample):
    """Updating a non-existent customer should return 404."""
    resp = await client.put(
        "/api/v1/customers/99999",
        json=customer_update_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


@pytest.mark.parametrize("payload", [
    {},  # missing name
    {"name": ""},  # empty name
])
async def test_update_customer_invalid_payload(client, auth_tokens, customer_sample, payload):
    """Updating a customer with invalid payload should fail."""
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    customer_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/customers/{customer_id}",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)


async def test_update_customer_unauthenticated(client, customer_update_sample):
    """Updating a customer without authentication should return 401."""
    resp = await client.put("/api/v1/customers/1", json=customer_update_sample, follow_redirects=True)
    assert resp.status_code == 401

@pytest.mark.parametrize("id", [
    'Abc',  # string instead of int
    -1,  # negative
])
async def test_update_customer_invalid_id(client, auth_tokens, customer_update_sample, id):
    """Updating a customer with invalid ID should return 400."""
    resp = await client.put(
        f"/api/v1/customers/{id}",
        json=customer_update_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code in (400, 422)

async def test_update_customer_no_changes(client, auth_tokens, customer_sample):
    """Updating a customer with no changes should succeed."""
    # Create a customer
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert create_resp.status_code == 201
    customer_id = create_resp.json()["id"]

    # Update the customer with the same data
    resp = await client.put(
        f"/api/v1/customers/{customer_id}",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    updated_customer = resp.json()
    assert updated_customer["name"] == customer_sample["name"]
    assert updated_customer["id"] == customer_id


# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_delete_customer_success(client, auth_tokens, customer_sample, role):
    """All roles should be able to delete a customer."""
    # Create a customer
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert create_resp.status_code == 201
    customer_id = create_resp.json()["id"]

    # Delete the customer
    resp = await client.delete(
        f"/api/v1/customers/{customer_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 204

    # Verify deletion
    get_resp = await client.get(
        f"/api/v1/customers/{customer_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert get_resp.status_code == 404


async def test_delete_customer_not_found(client, auth_tokens):
    """Deleting a non-existent customer should return 404."""
    resp = await client.delete(
        "/api/v1/customers/99999",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


async def test_delete_customer_unauthenticated(client):
    """Deleting a customer without authentication should return 401."""
    resp = await client.delete("/api/v1/customers/1", follow_redirects=True)
    assert resp.status_code == 401

# ---------------------------
# ATTACH CARD TO CUSTOMER TESTS
# ---------------------------

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_attach_card_to_customer_success(client, auth_tokens, customer_sample, role):
    """All roles should be able to attach a card to a customer."""
    # Create customer
    cust_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    customer_id = cust_resp.json()["id"]

    # Create card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

    # Attach card to customer
    resp = await client.patch(
        f"/api/v1/customers/{customer_id}/attach-card/{card_id}",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201

    res = await client.get(
        f"/api/v1/customers/{customer_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    customer = res.json() 

    assert customer["card"]["card_id"] == card_id


async def test_attach_card_customer_not_found(client, auth_tokens):
    """Attaching card to non-existent customer should return 404."""
    resp = await client.patch(
        "/api/v1/customers/99999/attach-card/0000000123",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


async def test_attach_card_not_found(client, auth_tokens, customer_sample):
    """Attaching non-existent card should return 404."""
    cust_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    customer_id = cust_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/customers/{customer_id}/attach-card/9999999999",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


async def test_attach_card_already_attached(client, auth_tokens, customer_sample):
    """Attaching already attached card should return 409."""
    # Create two customers
    cust1_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    customer1_id = cust1_resp.json()["id"]

    cust2_resp = await client.post(
        "/api/v1/customers",
        json={"name": "Customer 2"},
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    customer2_id = cust2_resp.json()["id"]

    # Create card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

    # Attach to first customer
    await client.patch(
        f"/api/v1/customers/{customer1_id}/attach-card/{card_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    # Try to attach to second
    resp = await client.patch(
        f"/api/v1/customers/{customer2_id}/attach-card/{card_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 409


async def test_attach_card_unauthenticated(client):
    """Attaching card without authentication should return 401."""
    resp = await client.patch("/api/v1/customers/1/attach-card/0000000123", follow_redirects=True)
    assert resp.status_code == 401


async def test_modify_card_points_add(client, auth_tokens):
    """Adding points to a card should succeed."""
    # Create card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

    # Add points
    resp = await client.patch(
        f"/api/v1/customers/cards/{card_id}?points=10",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    card = resp.json()
    assert card["points"] == 10


async def test_modify_card_points_remove(client, auth_tokens):
    """Removing points from a card should succeed."""
    # Create card and add points
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

    await client.patch(
        f"/api/v1/customers/cards/{card_id}?points=20",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )

    # Remove points
    resp = await client.patch(
        f"/api/v1/customers/cards/{card_id}?points=-5",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    card = resp.json()
    assert card["points"] == 15


async def test_modify_card_points_insufficient(client, auth_tokens):
    """Removing more points than available should fail."""
    # Create card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin")
    )
    card_id = card_resp.json()["card_id"]

    # Try to remove points from zero
    resp = await client.patch(
        f"/api/v1/customers/cards/{card_id}?points=-5",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 500  # Insufficient points


@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
async def test_modify_card_points_as_role(client, auth_tokens, role):
    """All roles should be able to modify card points."""
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

    resp = await client.patch(
        f"/api/v1/customers/cards/{card_id}?points=5",
        headers=auth_header(auth_tokens, role),
        follow_redirects=True,
    )
    assert resp.status_code == 201


async def test_modify_card_points_not_found(client, auth_tokens):
    """Modifying points on non-existent card should return 404."""
    resp = await client.patch(
        "/api/v1/customers/cards/9999999999?points=10",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 404


async def test_modify_card_points_unauthenticated(client):
    """Modifying card points without authentication should return 401."""
    resp = await client.patch("/api/v1/customers/cards/0000000123?points=10", follow_redirects=True)
    assert resp.status_code == 401



# ---------------------------
# EDGE CASES & INTEGRATION TESTS
# ---------------------------

async def test_customer_lifecycle(client, auth_tokens):
    """Test complete customer lifecycle: create, update, attach card, modify points, delete."""
    # Create customer
    customer_payload = {"name": "Lifecycle Test"}
    create_resp = await client.post(
        "/api/v1/customers",
        json=customer_payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert create_resp.status_code == 201
    customer = create_resp.json()
    customer_id = customer["id"]

    # Update customer
    update_payload = {"name": "Updated Lifecycle Test"}
    update_resp = await client.put(
        f"/api/v1/customers/{customer_id}",
        json=update_payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert update_resp.status_code == 201

    # Create and attach card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    card_id = card_resp.json()["card_id"]

    attach_resp = await client.patch(
        f"/api/v1/customers/{customer_id}/attach-card/{card_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert attach_resp.status_code == 201

    # Modify points
    points_resp = await client.patch(
        f"/api/v1/customers/cards/{card_id}?points=25",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert points_resp.status_code == 201

    # Delete customer (should also delete card)
    delete_resp = await client.delete(
        f"/api/v1/customers/{customer_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert delete_resp.status_code == 204

    # Verify customer deleted
    get_resp = await client.get(
        f"/api/v1/customers/{customer_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert get_resp.status_code == 404

    # Verify card also deleted (assuming cascade delete)
    # Note: swagger doesn't specify, but likely card is deleted with customer


async def test_create_customer_with_card_success(client, auth_tokens):
    """Creating a customer with a valid card should succeed."""
    # First create a card
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert card_resp.status_code == 201
    card = card_resp.json()
    card_id = card["card_id"]

    # Now create customer with that card
    payload = {
        "name": "Test Customer",
        "card": {
            "card_id": card_id,
            "points": 10
        }
    }
    resp = await client.post(
        "/api/v1/customers",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["card"]["card_id"] == card_id
    #verifying that the points received in input are ignored
    assert data["card"]["points"] == 0


async def test_create_customer_with_valid_card_already_assigned(client, auth_tokens, customer_sample):
    """Creating a customer with non-existent card should fail."""
    # First, create a card and assign to a customer
    card_resp = await client.post(
        "/api/v1/customers/cards",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    #then, create a customer
    card_id = card_resp.json()["card_id"]
    cust_resp = await client.post(
        "/api/v1/customers",
        json=customer_sample,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    #then attaching the card to the customer
    res = await client.patch(
        f"/api/v1/customers/{cust_resp.json()['id']}/attach-card/{card_id}",
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert res.status_code == 201

    payload = {
        "name": "Test Customer",
        "card": {
            "card_id": card_id,
            "points": 100
        }
    }
    resp = await client.post(
        "/api/v1/customers",
        json=payload,
        headers=auth_header(auth_tokens, "admin"),
        follow_redirects=True,
    )
    assert not resp.status_code == 201  # Should fail
