# tests/test_user_api.py
import asyncio
import pytest
import copy
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
    from main import app
    with TestClient(app) as c:
        yield c


BASE_URL = "http://127.0.0.1:8000/api/v1"


# ---------------------------
# GLOBAL FIXTURE FOR TOKENS
# ---------------------------



@pytest.fixture(scope="session", autouse=True)
def auth_tokens(event_loop, client):
    """Authenticate users once and return their JWT tokens."""

    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())
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
# LOCAL FIXTURE FOR RESETTING DB
# ---------------------------

@pytest.fixture(autouse=True)
def run_before_and_after_tests(event_loop):
    """Fixture to execute asserts before and after a test is run"""
    # reset db and ensure users are back 
    event_loop.run_until_complete(reset())
    event_loop.run_until_complete(init_db())

    yield

    # nothing after tests are done


# ---------------------------
# SAMPLE PAYLOADS
# ---------------------------

CUSTOMER_SAMPLE = {
    "name": "Mario Rossi"
}

CUSTOMER_SAMPLE_1 = {
    "name": "Paolo Bianchi"
}

CUSTOMER_SAMPLE_WITH_CARD = {
    "name": "Roberto Verdi",
    "card": {
        "card_id": "0000000123",
        "points": 120
    }
}


# ---------------------------
# CREATE CARD TESTS
# ---------------------------

def test_create_card_success_as_admin(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["card_id"] is not None
    assert data["points"] == 0
    
def test_create_card_success_as_cashier(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["card_id"] is not None
    assert data["points"] == 0
    
def test_create_card_success_as_manager(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["card_id"] is not None
    assert data["points"] == 0


def test_create_card_unauthenticated(client):
    resp = client.post(BASE_URL + "/customers/cards")
    assert resp.status_code == 401


# ---------------------------
# CREATE CUSTOMER TESTS
# ---------------------------

def test_create_customer_success_as_admin(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == CUSTOMER_SAMPLE["name"]
    assert data["id"] is not None
    
def test_create_customer_success_as_cashier(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == CUSTOMER_SAMPLE["name"]
    assert data["id"] is not None
    
def test_create_customer_success_as_manager(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == CUSTOMER_SAMPLE["name"]
    assert data["id"] is not None


def test_create_multiple_customers(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    resp1 = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp1.status_code == 201


def test_create_customer_missing_fields(client, auth_tokens):
    bad = {"name": ""}
    resp = client.post(BASE_URL + "/customers", json=bad, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code in (400, 422)
    

def test_create_customer_with_card(client, auth_tokens):
    # create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    
    # create a customer
    customer_json = copy.deepcopy(CUSTOMER_SAMPLE_WITH_CARD)
    customer_json["card"]["card_id"] = card["card_id"]

    resp = client.post(BASE_URL + "/customers", json=customer_json, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == customer_json["name"]
    assert data["id"] is not None
    assert data["card"] is not None
    
    assert data["card"]["card_id"] == card["card_id"]
    assert data["card"]["points"] == 0


def test_create_customer_with_wrong_card(client, auth_tokens):
    # create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    
    # create a customer 
    customer_1_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE,  headers=auth_header(auth_tokens, "admin"))
    customer_1 = customer_1_resp.json()
    
    # associate card to customer 1
    client.post(BASE_URL + f"customers/{customer_1["id"]}/attach-card/{card["card_id"]}")

    # create a second customer with customer 1's card
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]

    resp = client.post(BASE_URL + "/customers", json=customer_json, 
                       headers=auth_header(auth_tokens, "admin"))
    
    assert resp.status_code == 409


def test_create_customer_unauthenticated(client):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE)
    assert resp.status_code == 401


# ---------------------------
# LIST CUSTOMERS TESTS
# ---------------------------

def test_list_customers_success_as_admin(client, auth_tokens):
    resp = client.get(BASE_URL + "/customers", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_list_customers_success_as_cashier(client, auth_tokens):
    resp = client.get(BASE_URL + "/customers", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_list_customers_success_as_manager(client, auth_tokens):
    resp = client.get(BASE_URL + "/customers", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_list_customers_empty(client, auth_tokens):
    resp = client.get(BASE_URL + "/customers", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert resp.json() == []

def test_list_customers_not_empty(client, auth_tokens):
    customer = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin")).json()
    customer_1 = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE_1, headers=auth_header(auth_tokens, "admin")).json()

    resp = client.get(BASE_URL + "/customers", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert customer in resp.json()
    assert customer_1 in resp.json()

def test_list_customers_unauthenticated(client):
    resp = client.get(BASE_URL + "/customers")
    assert resp.status_code == 401


# ---------------------------
# GET CUSTOMER BY ID TESTS
# ---------------------------

def test_get_customer_success_as_admin(client, auth_tokens):
    client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))

    resp = client.get(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200

def test_get_customer_success_as_admin(client, auth_tokens):
    client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))

    resp = client.get(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 200

def test_get_customer_success_as_admin(client, auth_tokens):
    client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))

    resp = client.get(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 200

def test_get_customer_invalid_id(client, auth_tokens):
    resp = client.get(BASE_URL + "/customers/-1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400

def test_get_customer_not_found(client, auth_tokens):
    resp = client.get(BASE_URL + "/customers/9999", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_get_customer_unauthenticated(client):
    resp = client.get(BASE_URL + "/customers/1")
    assert resp.status_code == 401


# ---------------------------
# UPDATE CUSTOMER TESTS
# ---------------------------
# TODO

# def test_update_user_success(client, auth_tokens):
#     payload = USER_SAMPLE.copy()
#     payload["username"] = "updated_user"
#     resp = client.put(BASE_URL + "/users/1", json=payload, headers=auth_header(auth_tokens, "admin"))
#     assert resp.status_code in (201, 404)
#     if resp.status_code == 201:
#         assert resp.json()["username"] == "updated_user"


# def test_update_user_not_found(client, auth_tokens):
#     payload = USER_SAMPLE.copy()
#     resp = client.put(BASE_URL + "/users/9999", json=payload, headers=auth_header(auth_tokens, "admin"))
#     assert resp.status_code == 404


# def test_update_user_conflict(client, auth_tokens):
#     payload = USER_ADMIN.copy()
#     resp = client.put(BASE_URL + "/users/1", json=payload, headers=auth_header(auth_tokens, "admin"))
#     if resp.status_code != 404:
#         assert resp.status_code == 409

# def test_update_user_unauthenticated(client):
#     resp = client.put(BASE_URL + "/users/1", json=USER_SAMPLE)
#     assert resp.status_code == 401


# def test_update_user_forbidden_as_cashier(client, auth_tokens):
#     resp = client.put(BASE_URL + "/users/1", json=USER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
#     assert resp.status_code == 403


# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------

def test_delete_customer_success_as_admin(client, auth_tokens):
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    customer = customer_resp.json()

    resp = client.delete(BASE_URL + f"/customers/{customer["id"]}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 204
    

def test_delete_customer_success_as_cashier(client, auth_tokens):
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    customer = customer_resp.json()

    resp = client.delete(BASE_URL + f"/customers/{customer["id"]}", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 204
    

def test_delete_customer_success_as_manager(client, auth_tokens):
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    customer = customer_resp.json()

    resp = client.delete(BASE_URL + f"/customers/{customer["id"]}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 204


def test_delete_customer_not_found(client, auth_tokens):
    resp = client.delete(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    customer = customer_resp.json()

    resp = client.delete(BASE_URL + f"/customers/{customer["id"] + 1}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 404


def test_delete_customer_unauthenticated(client):
    resp = client.delete(BASE_URL + "/customers/1")
    assert resp.status_code == 401


# ---------------------------
# ATTACH CARD TESTS
# ---------------------------

def test_attach_card_to_customer_success_as_admin(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]

	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    customer = customer_resp.json()
    customer_id = customer["id"]

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    

def test_attach_card_to_customer_success_as_cashier(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "cashier"))
    card = card_resp.json()
    card_id = card["card_id"]

	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    customer = customer_resp.json()
    customer_id = customer["id"]

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    

def test_attach_card_to_customer_success_as_manager(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    card_id = card["card_id"]

	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    customer = customer_resp.json()
    customer_id = customer["id"]

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201

def test_attach_card_to_customer_invalid_customer_id(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    card_id = card["card_id"]

    resp = client.patch(BASE_URL + f"/customers/{-1}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400
    

def test_attach_card_to_customer_invalid_card_id(client, auth_tokens):
	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    customer = customer_resp.json()
    customer_id = customer["id"]

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{-1}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400


def test_attach_card_to_customer_card_not_found(client, auth_tokens):

	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    customer = customer_resp.json()
    customer_id = customer["id"]

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/9999", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    

def test_attach_card_to_customer_customer_not_found(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    card_id = card["card_id"]

    resp = client.patch(BASE_URL + f"/customers/{9999}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_attach_card_to_customer_card_already_attached(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    card_id = card["card_id"]

	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    customer = customer_resp.json()
    customer_id = customer["id"]

	# create a second customer
    customer_resp_1 = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE_1, headers=auth_header(auth_tokens, "admin"))
    customer_1 = customer_resp_1.json()
    customer_id_1 = customer_1["id"]

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201

	resp = client.patch(BASE_URL + f"/customers/{customer_id_1}/attach-card/{card_id}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 409
    

def test_attach_card_to_customer_customer_unauthenticated(client):
    resp = client.patch(BASE_URL + f"/customers/1/attach-card/1")
    assert resp.status_code == 401


# ---------------------------
# MODIFY CARD POINTS TESTS
# ---------------------------

def test_modify_card_points_success_as_admin(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]

	# modify points a few times
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 100
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-90}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 10
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-10}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 0
    

def test_modify_card_points_success_as_cashier(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "cashier"))
    card = card_resp.json()
    card_id = card["card_id"]

	# modify points a few times
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={100}", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 100
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-90}", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 10
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-10}", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 0
    

def test_modify_card_points_success_as_manager(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    card_id = card["card_id"]

	# modify points a few times
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={100}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 100
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-90}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 10
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-10}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 0
    

def test_modify_card_points_invalid_id(client, auth_tokens):
    resp = client.patch(BASE_URL + f"/customers/cards/{-1}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400


def test_modify_card_points_card_not_found(client, auth_tokens):
    resp = client.patch(BASE_URL + f"/customers/cards/{9999}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_modify_card_points_success_as_manager(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]

    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 100
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-101}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 500


def test_modify_card_points_success_unauthenticated(client):
    resp = client.patch(BASE_URL + f"/customers/cards/1?points={100}")
    assert resp.status_code == 401
