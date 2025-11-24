# tests/test_user_api.py
import pytest
from fastapi.testclient import TestClient
from main import app
from init_db import reset, init_db

client = TestClient(app)
BASE_URL = "http://127.0.0.1:8000/api/v1"


# ---------------------------
# GLOBAL FIXTURE FOR TOKENS
# ---------------------------

@pytest.fixture(scope="session", autouse=True)
def auth_tokens():
    """Authenticate users once and return their JWT tokens."""

    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(reset())
    loop.run_until_complete(init_db())

    users = {
        "admin": {"username": "admin", "password": "admin"},
        "manager": {"username": "ShopManager", "password": "ShManager"},
        "cashier": {"username": "Cashier", "password": "Cashier"},
    }

    tokens = {}
    for role, creds in users.items():
        response = client.post(BASE_URL + "/auth", json=creds)
        assert response.status_code == 200, f"Login failed for {role}"
        tokens[role] = f"Bearer {response.json()['token']}"

    return tokens


def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}


# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

USER_SAMPLE = {
    "username": "new_user",
    "password": "NewPass123!",
    "type": "Cashier",
}

USER_ADMIN = {
    "username": "admin",
    "password": "SecurePass123!",
    "type": "Administrator",
}


# ---------------------------
# CREATE USER TESTS
# ---------------------------

def test_create_user_success_as_admin(auth_tokens):
    resp = client.post(BASE_URL + "/users", json=USER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == USER_SAMPLE["username"]
    assert data["type"] == USER_SAMPLE["type"]


def test_create_user_conflict(auth_tokens):
    resp = client.post(BASE_URL + "/users", json=USER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 409


def test_create_user_missing_fields(auth_tokens):
    bad = {"username": "incomplete"}
    resp = client.post(BASE_URL + "/users", json=bad, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code in (400, 422)


def test_create_user_unauthenticated():
    resp = client.post(BASE_URL + "/users", json=USER_SAMPLE)
    assert resp.status_code == 401


def test_create_user_forbidden_as_cashier(auth_tokens):
    resp = client.post(BASE_URL + "/users", json=USER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# LIST USERS TESTS
# ---------------------------

def test_list_users_success_as_admin(auth_tokens):
    resp = client.get(BASE_URL + "/users", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_users_unauthenticated():
    resp = client.get(BASE_URL + "/users")
    assert resp.status_code == 401


def test_list_users_forbidden_as_cashier(auth_tokens):
    resp = client.get(BASE_URL + "/users", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# GET USER BY ID TESTS
# ---------------------------

def test_get_user_success(auth_tokens):
    resp = client.get(BASE_URL + "/users/1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert "id" in resp.json()


def test_get_user_not_found(auth_tokens):
    resp = client.get(BASE_URL + "/users/9999", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_get_user_unauthenticated():
    resp = client.get(BASE_URL + "/users/1")
    assert resp.status_code == 401


def test_get_user_forbidden_as_cashier(auth_tokens):
    resp = client.get(BASE_URL + "/users/1", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# UPDATE USER TESTS
# ---------------------------

def test_update_user_success(auth_tokens):
    payload = USER_SAMPLE.copy()
    payload["username"] = "updated_user"
    resp = client.put(BASE_URL + "/users/1", json=payload, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code in (201, 404)
    if resp.status_code == 201:
        assert resp.json()["username"] == "updated_user"


def test_update_user_not_found(auth_tokens):
    payload = USER_SAMPLE.copy()
    resp = client.put(BASE_URL + "/users/9999", json=payload, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_update_user_conflict(auth_tokens):
    payload = USER_ADMIN.copy()
    resp = client.put(BASE_URL + "/users/1", json=payload, headers=auth_header(auth_tokens, "admin"))
    if resp.status_code != 404:
        assert resp.status_code == 409

def test_update_user_unauthenticated():
    resp = client.put(BASE_URL + "/users/1", json=USER_SAMPLE)
    assert resp.status_code == 401


def test_update_user_forbidden_as_cashier(auth_tokens):
    resp = client.put(BASE_URL + "/users/1", json=USER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


# ---------------------------
# DELETE USER TESTS
# ---------------------------

def test_delete_user_success(auth_tokens):
    resp = client.delete(BASE_URL + "/users/1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code in (204, 404)


def test_delete_user_unauthenticated():
    resp = client.delete(BASE_URL + "/users/1")
    assert resp.status_code == 401


def test_delete_user_forbidden_as_cashier(auth_tokens):
    resp = client.delete(BASE_URL + "/users/1", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 403


def test_delete_user_not_found(auth_tokens):
    resp = client.delete(BASE_URL + "/users/9999", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
