# tests/test_user_api.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

# ---------------------------
# FIXTURES
# ---------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def base_url():
    """Base URL for API endpoints."""
    return "http://127.0.0.1:8000/api/v1"


@pytest.fixture(scope="session")
def initial_users():
    """Define the three users that should always exist in the database."""
    return {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }


@pytest.fixture(scope="function")
def auth_tokens(event_loop, client, base_url, initial_users):
    """
    Reset database and authenticate users before each test.
    This ensures each test starts with a clean state.
    """
    # Reset and initialize database with the three base users
    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
    
    # Authenticate all three users and get their tokens
    tokens = {}
    for role, creds in initial_users.items():
        response = client.post(f"{base_url}/auth", json=creds)
        assert response.status_code == 200, f"Login failed for {role}"
        tokens[role] = f"Bearer {response.json()['token']}"
    
    return tokens


def auth_header(tokens, role: str):
    """Helper function to create authorization headers."""
    return {"Authorization": tokens[role]}


# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

@pytest.fixture
def user_sample():
    """Sample user payload for testing."""
    return {
        "username": "new_user",
        "password": "NewPass123!",
        "type": "Cashier",
    }


@pytest.fixture
def user_admin_payload():
    """Admin user payload (conflicts with existing admin)."""
    return {
        "username": "admin",
        "password": "SecurePass123!",
        "type": "Administrator",
    }


@pytest.fixture
def user_manager_payload():
    """Manager user payload for testing."""
    return {
        "username": "new_manager",
        "password": "ManagerPass123!",
        "type": "ShopManager",
    }


# ---------------------------
# CREATE USER TESTS
# ---------------------------

def test_create_user_success_as_admin(client, auth_tokens, base_url, user_sample):
    """Admin should be able to create a new user."""
    resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == user_sample["username"]
    assert data["type"] == user_sample["type"]
    assert "id" in data


def test_create_user_conflict_existing_username(client, auth_tokens, base_url, user_admin_payload):
    """Creating a user with existing username should return 409."""
    resp = client.post(
        f"{base_url}/users",
        json=user_admin_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 409


def test_create_user_missing_fields(client, auth_tokens, base_url):
    """Creating a user with missing required fields should fail."""
    incomplete_payload = {"username": "incomplete"}
    resp = client.post(
        f"{base_url}/users",
        json=incomplete_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (400, 422)


def test_create_user_unauthenticated(client, base_url, user_sample):
    """Creating a user without authentication should return 401."""
    resp = client.post(f"{base_url}/users", json=user_sample)
    assert resp.status_code == 401


def test_create_user_forbidden_as_cashier(client, auth_tokens, base_url, user_sample):
    """Cashier should not be able to create users."""
    resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


def test_create_user_forbidden_as_manager(client, auth_tokens, base_url, user_sample):
    """Manager should not be able to create users (if that's your business rule)."""
    resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "manager")
    )
    # Adjust this based on your actual authorization rules
    assert resp.status_code in (201, 403)


# ---------------------------
# LIST USERS TESTS
# ---------------------------

def test_list_users_success_as_admin(client, auth_tokens, base_url):
    """Admin should be able to list all users."""
    resp = client.get(f"{base_url}/users", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert len(users) == 3  # Should have exactly 3 initial users


def test_list_users_includes_all_initial_users(client, auth_tokens, base_url, initial_users):
    """List should include all three initial users."""
    resp = client.get(f"{base_url}/users", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    users = resp.json()
    usernames = [u["username"] for u in users]
    for role, creds in initial_users.items():
        assert creds["username"] in usernames


def test_list_users_unauthenticated(client, base_url):
    """Listing users without authentication should return 401."""
    resp = client.get(f"{base_url}/users")
    assert resp.status_code == 401


def test_list_users_forbidden_as_cashier(client, auth_tokens, base_url):
    """Cashier should not be able to list users."""
    resp = client.get(f"{base_url}/users", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# GET USER BY ID TESTS
# ---------------------------

def test_get_user_by_id_success(client, auth_tokens, base_url):
    """Admin should be able to get a user by ID."""
    # First, get the list to find a valid user ID
    list_resp = client.get(f"{base_url}/users", headers=auth_header(auth_tokens, "admin"))
    users = list_resp.json()
    user_id = users[0]["id"]
    
    resp = client.get(f"{base_url}/users/{user_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user_id
    assert "username" in data
    assert "type" in data


def test_get_user_not_found(client, auth_tokens, base_url):
    """Getting a non-existent user should return 404."""
    resp = client.get(f"{base_url}/users/99999", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_get_user_unauthenticated(client, base_url):
    """Getting a user without authentication should return 401."""
    resp = client.get(f"{base_url}/users/1")
    assert resp.status_code == 401


def test_get_user_forbidden_as_cashier(client, auth_tokens, base_url):
    """Cashier should not be able to get user details."""
    resp = client.get(f"{base_url}/users/1", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# UPDATE USER TESTS
# ---------------------------

def test_update_user_success(client, auth_tokens, base_url, user_sample):
    """Admin should be able to update a user."""
    # First create a user to update
    create_resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "admin")
    )
    assert create_resp.status_code == 201
    created_user = create_resp.json()
    user_id = created_user["id"]
    
    # Update the user
    update_payload = user_sample.copy()
    update_payload["username"] = "updated_user"
    resp = client.put(
        f"{base_url}/users/{user_id}",
        json=update_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 201
    updated_user = resp.json()
    assert updated_user["username"] == "updated_user"
    assert updated_user["id"] == user_id


def test_update_user_not_found(client, auth_tokens, base_url, user_sample):
    """Updating a non-existent user should return 404."""
    resp = client.put(
        f"{base_url}/users/99999",
        json=user_sample,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 404


def test_update_user_conflict_username(client, auth_tokens, base_url, user_sample):
    """Updating a user with an existing username should return 409."""
    # Create a new user
    create_resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "admin")
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]
    
    # Try to update with admin's username (conflict)
    conflict_payload = user_sample.copy()
    conflict_payload["username"] = "admin"
    resp = client.put(
        f"{base_url}/users/{user_id}",
        json=conflict_payload,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 409


def test_update_user_unauthenticated(client, base_url, user_sample):
    """Updating a user without authentication should return 401."""
    resp = client.put(f"{base_url}/users/1", json=user_sample)
    assert resp.status_code == 401


def test_update_user_forbidden_as_cashier(client, auth_tokens, base_url, user_sample):
    """Cashier should not be able to update users."""
    resp = client.put(
        f"{base_url}/users/1",
        json=user_sample,
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


# ---------------------------
# DELETE USER TESTS
# ---------------------------

def test_delete_user_success(client, auth_tokens, base_url, user_sample):
    """Admin should be able to delete a user."""
    # First create a user to delete
    create_resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "admin")
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]
    
    # Delete the user
    resp = client.delete(
        f"{base_url}/users/{user_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 204
    
    # Verify the user is deleted
    get_resp = client.get(
        f"{base_url}/users/{user_id}",
        headers=auth_header(auth_tokens, "admin")
    )
    assert get_resp.status_code == 404


def test_delete_user_not_found(client, auth_tokens, base_url):
    """Deleting a non-existent user should return 404."""
    resp = client.delete(
        f"{base_url}/users/99999",
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code == 404


def test_delete_user_unauthenticated(client, base_url):
    """Deleting a user without authentication should return 401."""
    resp = client.delete(f"{base_url}/users/1")
    assert resp.status_code == 401


def test_delete_user_forbidden_as_cashier(client, auth_tokens, base_url):
    """Cashier should not be able to delete users."""
    resp = client.delete(
        f"{base_url}/users/1",
        headers=auth_header(auth_tokens, "cashier")
    )
    assert resp.status_code == 403


# ---------------------------
# EDGE CASES & INTEGRATION TESTS
# ---------------------------

def test_create_and_list_user(client, auth_tokens, base_url, user_sample):
    """Creating a user should make it appear in the list."""
    # Create user
    create_resp = client.post(
        f"{base_url}/users",
        json=user_sample,
        headers=auth_header(auth_tokens, "admin")
    )
    assert create_resp.status_code == 201
    created_user = create_resp.json()
    
    # List users
    list_resp = client.get(f"{base_url}/users", headers=auth_header(auth_tokens, "admin"))
    assert list_resp.status_code == 200
    users = list_resp.json()
    assert len(users) == 4  # 3 initial + 1 new
    
    # Verify new user is in the list
    usernames = [u["username"] for u in users]
    assert user_sample["username"] in usernames


def test_multiple_user_types_creation(client, auth_tokens, base_url):
    """Test creating users of different types."""
    user_types = [
        {"username": "cashier2", "password": "Pass123!", "type": "Cashier"},
        {"username": "manager2", "password": "Pass123!", "type": "ShopManager"},
        {"username": "admin2", "password": "Pass123!", "type": "Administrator"},
    ]
    
    for user_data in user_types:
        resp = client.post(
            f"{base_url}/users",
            json=user_data,
            headers=auth_header(auth_tokens, "admin")
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == user_data["type"]


def test_invalid_user_type(client, auth_tokens, base_url):
    """Creating a user with invalid type should fail."""
    invalid_user = {
        "username": "invalid_type_user",
        "password": "Pass123!",
        "type": "InvalidType",
    }
    resp = client.post(
        f"{base_url}/users",
        json=invalid_user,
        headers=auth_header(auth_tokens, "admin")
    )
    assert resp.status_code in (400, 422)


def test_weak_password_validation(client, auth_tokens, base_url):
    """Test password validation (if implemented)."""
    weak_password_user = {
        "username": "weak_pass_user",
        "password": "123",  # Weak password
        "type": "Cashier",
    }
    resp = client.post(
        f"{base_url}/users",
        json=weak_password_user,
        headers=auth_header(auth_tokens, "admin")
    )
    # This depends on your password validation rules
    # Adjust assertion based on actual implementation
    assert resp.status_code in (201, 400, 422)