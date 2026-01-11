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
def reset_db_but_keep_users(event_loop):
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
        "card_id": "0000000001",
        "points": 0
    }
}

CUSTOMER_UPDATED_SAMPLE = {
    "name": "Mario Rossi Aggiornato"
}

CUSTOMER_UPDATED_SAMPLE_WITH_CARD = {
    "name": "Roberto Verdi Aggiornato",
    "card": {
        "card_id": "0000000001",
        "points": 230
    }
}


# ---------------------------
# CREATE CARD TESTS
# ---------------------------

def test_create_card_success_as_admin(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    card = resp.json()
    assert card["card_id"] is not None
    assert card["points"] == 0
    
def test_create_card_success_as_cashier(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    card = resp.json()
    assert card["card_id"] is not None
    assert card["points"] == 0
    
def test_create_card_success_as_manager(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 201
    card = resp.json()
    assert card["card_id"] is not None
    assert card["points"] == 0


def test_create_card_unauthenticated(client):
    resp = client.post(BASE_URL + "/customers/cards")
    assert resp.status_code == 401


# ---------------------------
# CREATE CUSTOMER TESTS
# ---------------------------

def test_create_customer_success_as_admin(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    customer = resp.json()
    assert customer["name"] == CUSTOMER_SAMPLE["name"]
    assert customer["id"] is not None
    
def test_create_customer_success_as_cashier(client, auth_tokens):
    resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 201
    customer = resp.json()
    assert customer["name"] == CUSTOMER_SAMPLE["name"]
    assert customer["id"] is not None
    
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
    customer = resp.json()
    assert customer["name"] == customer_json["name"]
    assert customer["id"] is not None
    assert customer["card"] is not None
    
    assert customer["card"]["card_id"] == card["card_id"]
    assert customer["card"]["points"] == 0


def test_create_customer_with_invalid_card(client, auth_tokens):
	# create a customer with a card that doesn't exist
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = -1

    resp = client.post(BASE_URL + "/customers", json=customer_json, 
                       headers=auth_header(auth_tokens, "admin"))
    
    assert resp.status_code == 400
    

def test_create_customer_with_wrong_card(client, auth_tokens):
	# create a customer with a card that doesn't exist
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = 9999


    resp = client.post(BASE_URL + "/customers", json=customer_json, 
                       headers=auth_header(auth_tokens, "admin"))
    
    assert resp.status_code == 400
    

def test_create_customer_card_conflict(client, auth_tokens):
    # create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "manager"))
    card = card_resp.json()
    
    # create a customer 
    customer_1_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE,  headers=auth_header(auth_tokens, "admin"))
    customer_1 = customer_1_resp.json()
    
    # associate card to customer 1
    customer_1_id = customer_1["id"]
    card_id = card["card_id"]
    resp = client.patch(BASE_URL + f"/customers/{customer_1_id}/attach-card/{card_id}",  headers=auth_header(auth_tokens, "admin"))

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
    # create customers to retrieve
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
    # create customer to retrieve
    client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))

    resp = client.get(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 200

def test_get_customer_success_as_cashier(client, auth_tokens):
    # create customer to retrieve
	client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))

	resp = client.get(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "cashier"))
	assert resp.status_code == 200

def test_get_customer_success_as_manager(client, auth_tokens):
    # create customer to retrieve
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

def test_update_customer_success_as_admin(client, auth_tokens):
    # create customer to update
    customer = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin")).json()
    customer_id = customer["id"]
	# update customer
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=CUSTOMER_UPDATED_SAMPLE,
                    headers=auth_header(auth_tokens, "admin"))
    
    assert resp.status_code == 201
    assert resp.json()["name"] == CUSTOMER_UPDATED_SAMPLE["name"]
    

def test_update_customer_success_as_cashier(client, auth_tokens):
    # create customer to update
    customer = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, 
                        headers=auth_header(auth_tokens, "cashier")).json()
    customer_id = customer["id"]
	# update customer
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=CUSTOMER_UPDATED_SAMPLE,
                    headers=auth_header(auth_tokens, "cashier"))
    
    assert resp.status_code == 201
    assert resp.json()["name"] == CUSTOMER_UPDATED_SAMPLE["name"]


def test_update_customer_success_as_manager(client, auth_tokens):
    # create customer to update
    customer = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, 
                        headers=auth_header(auth_tokens, "manager")).json()
    
	# update customer
    customer_id = customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=CUSTOMER_UPDATED_SAMPLE,
                    headers=auth_header(auth_tokens, "manager"))
    
    assert resp.status_code == 201
    assert resp.json()["name"] == CUSTOMER_UPDATED_SAMPLE["name"]


def test_update_customer_invalid_customer(client, auth_tokens):
	# update a customer that doesn't exist
    resp = client.put(BASE_URL + "/customers/-1", json=CUSTOMER_UPDATED_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400


def test_update_customer_not_found(client, auth_tokens):
	# update a customer that doesn't exist
    resp = client.put(BASE_URL + "/customers/9999", json=CUSTOMER_UPDATED_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    

def test_update_customer_with_card_success(client, auth_tokens):
	# create card
    card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to update
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]
    customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()
    
    # update customer and check all info was updated
    customer_id = customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=CUSTOMER_UPDATED_SAMPLE_WITH_CARD,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    
    updated_customer = resp.json()
    assert updated_customer["name"] == CUSTOMER_UPDATED_SAMPLE_WITH_CARD["name"]
    assert updated_customer["card"]["card_id"] == int(CUSTOMER_UPDATED_SAMPLE_WITH_CARD["card"]["card_id"])
    assert updated_customer["card"]["points"] == int(CUSTOMER_UPDATED_SAMPLE_WITH_CARD["card"]["points"])
    

def test_update_customer_invalid_card(client, auth_tokens):
	# create card
    card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to update
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]
    customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()
    
	# update customer with an invalid card
    updated_customer = copy.deepcopy(CUSTOMER_UPDATED_SAMPLE_WITH_CARD)
    updated_customer["card"]["card_id"] = -1
    customer_id = customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=updated_customer,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400


def test_update_customer_card_not_found(client, auth_tokens):
	# create customer to update
    customer = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, 
                        headers=auth_header(auth_tokens, "admin")).json()
    
	# update customer with a card that doesn't exist

    customer_id = customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=CUSTOMER_UPDATED_SAMPLE_WITH_CARD,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    

def test_update_customer_empty_card(client, auth_tokens):
    # create card
    card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to update
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]
    customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()

    card_id = customer["card"]["card_id"]

    # update customer with an empty card, so its card should be deleted
    updated_customer = copy.deepcopy(CUSTOMER_UPDATED_SAMPLE)
    updated_customer["card"] = {} 
    customer_id =customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=updated_customer,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    actual_updated_customer = resp.json()
    assert actual_updated_customer["name"] == updated_customer["name"] 
    assert "card" not in actual_updated_customer or actual_updated_customer["card"] is None
        
    # if the original card has been deleted, trying to attach it to a customer should result in a not found 
    customer_1 =  client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin")).json()
    customer_1_id = customer_1["id"]
    resp = client.patch(BASE_URL + f"/customers/{customer_1_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    

def test_update_customer_empty_card_1(client, auth_tokens):
    # create card
    card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to update
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]
    customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()
        
    card_id = customer["card"]["card_id"]

    # update customer with None for card, so card should not be deleted
    updated_customer = copy.deepcopy(CUSTOMER_UPDATED_SAMPLE)
    updated_customer["card"] = None
    customer_id = customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=updated_customer,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    actual_updated_customer = resp.json()
    assert actual_updated_customer["name"] == updated_customer["name"] 
    assert "card" in actual_updated_customer
        
    # if the original card has not been deleted, trying to attach it to a customer should result in a conflict found 
    customer_1 =  client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin")).json()
    customer_1_id = customer_1["id"]
    resp = client.patch(BASE_URL + f"/customers/{customer_1_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 409
    

def test_update_customer_change_card(client, auth_tokens):
    # create card
    card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to update
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]
    customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()
    card_id = customer["card"]["card_id"]

    # create another card
    card_1 = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
    card_id_1 = card_1["card_id"]

    # update customer with new card, so its card should be deleted
    updated_customer = copy.deepcopy(CUSTOMER_UPDATED_SAMPLE_WITH_CARD)
    updated_customer["card"]["card_id"] = card_id_1
    updated_customer["card"]["points"] = 1000
    customer_id = customer["id"]
    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=updated_customer,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    actual_updated_customer = resp.json()
    assert actual_updated_customer["name"] == updated_customer["name"] 
    assert actual_updated_customer["card"]["card_id"] == updated_customer["card"]["card_id"]
    assert actual_updated_customer["card"]["points"] == updated_customer["card"]["points"]
        
    # if the original card has been deleted, trying to attach it to a customer should result in a not found 
    customer_1 =  client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin")).json()
    customer_1_id = customer_1["id"]
    resp = client.patch(BASE_URL + f"/customers/{customer_1_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    

def test_update_customer_conflict(client, auth_tokens):
	# create card
	card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to create a conflict with
	customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
	customer_json["card"]["card_id"] = card["card_id"]
	customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()
	customer_id = customer["id"]
	card_id = customer["card"]["card_id"]
     
	# create customer to update
	customer_1 = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, 
                        headers=auth_header(auth_tokens, "admin")).json()
	customer_id_1 = customer_1["id"]

	# update customer 1 with new card, so it should raise a conflict
	updated_customer = copy.deepcopy(CUSTOMER_UPDATED_SAMPLE_WITH_CARD)
	updated_customer["card"]["card_id"] = card_id
	updated_customer["card"]["points"] = 1000
	resp = client.put(BASE_URL + f"/customers/{customer_id_1}", json=updated_customer,
                    headers=auth_header(auth_tokens, "admin"))
	assert resp.status_code == 409
     
	# ensure original customer has its card and the points amount did not change
	resp = client.get(BASE_URL + f"/customers/{customer_id}", headers=auth_header(auth_tokens, "admin"))
	assert resp.status_code == 200
	original_customer = resp.json()
	assert original_customer["card"]["card_id"] == card_id
	assert original_customer["card"]["points"] == customer["card"]["points"]



def test_update_customer_with_card_negative_points(client, auth_tokens):
    # create card
    card = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin")).json()
	
	# create customer to update
    customer_json = CUSTOMER_SAMPLE_WITH_CARD.copy()
    customer_json["card"]["card_id"] = card["card_id"]
    customer = client.post(BASE_URL + "/customers", json=customer_json, 
                        headers=auth_header(auth_tokens, "admin")).json()
    
    # set updated card points to be negative, it should result in an error
    updated_customer = copy.deepcopy(CUSTOMER_UPDATED_SAMPLE_WITH_CARD)
    updated_customer["card"]["points"] = -100
    customer_id = customer["id"]

    resp = client.put(BASE_URL + f"/customers/{customer_id}", json=updated_customer,
                    headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400


def test_update_customer_unauthenticated(client):
    resp = client.put(BASE_URL + "/customers/1", json=CUSTOMER_UPDATED_SAMPLE)
    assert resp.status_code == 401



# ---------------------------
# DELETE CUSTOMER TESTS
# ---------------------------

def test_delete_customer_success_as_admin(client, auth_tokens):
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    customer = customer_resp.json()
    customer_id = customer["id"]
    resp = client.delete(BASE_URL + f"/customers/{customer_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 204
    

def test_delete_customer_success_as_cashier(client, auth_tokens):
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "cashier"))
    customer = customer_resp.json()
    customer_id = customer["id"]
    resp = client.delete(BASE_URL + f"/customers/{customer_id}", headers=auth_header(auth_tokens, "cashier"))
    assert resp.status_code == 204
    

def test_delete_customer_success_as_manager(client, auth_tokens):
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    customer = customer_resp.json()
    customer_id = customer["id"]
    resp = client.delete(BASE_URL + f"/customers/{customer_id}", headers=auth_header(auth_tokens, "manager"))
    assert resp.status_code == 204


def test_delete_customer_not_found(client, auth_tokens):
    resp = client.delete(BASE_URL + "/customers/1", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404
    
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "manager"))
    customer = customer_resp.json()
    customer_id = customer["id"]
    resp = client.delete(BASE_URL + f"/customers/{customer_id + 1}", headers=auth_header(auth_tokens, "manager"))
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

def test_attach_card_to_customer_invalid_customer(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]

    resp = client.patch(BASE_URL + f"/customers/{-1}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400
    

def test_attach_card_to_customer_invalid_card(client, auth_tokens):
	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
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
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]

    resp = client.patch(BASE_URL + f"/customers/{9999}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_attach_card_to_customer_card_already_attached(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
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

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201

    resp = client.patch(BASE_URL + f"/customers/{customer_id_1}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 409
    

def test_attach_card_to_customer_twice(client, auth_tokens):
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

    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    

def test_attach_card_to_customer_customer_already_has_card(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]
    
	# create a second card
    card_resp_1 = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card_1 = card_resp_1.json()
    card_id_1 = card_1["card_id"]

	# create a customer
    customer_resp = client.post(BASE_URL + "/customers", json=CUSTOMER_SAMPLE, headers=auth_header(auth_tokens, "admin"))
    customer = customer_resp.json()
    customer_id = customer["id"]

	# attach one card
    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201

	# attach other card
    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id_1}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    
	# attach first card again (since it is not deleted, this should work)
    resp = client.patch(BASE_URL + f"/customers/{customer_id}/attach-card/{card_id}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    

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
    

def test_modify_card_points_insufficient_points(client, auth_tokens):
	# create a card
    card_resp = client.post(BASE_URL + "/customers/cards", headers=auth_header(auth_tokens, "admin"))
    card = card_resp.json()
    card_id = card["card_id"]

    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 201
    assert resp.json()["points"] == 100
    resp = client.patch(BASE_URL + f"/customers/cards/{card_id}?points={-101}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 500


def test_modify_card_points_invalid_id(client, auth_tokens):
    resp = client.patch(BASE_URL + f"/customers/cards/{-1}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 400


def test_modify_card_points_card_not_found(client, auth_tokens):
    resp = client.patch(BASE_URL + f"/customers/cards/{9999}?points={100}", headers=auth_header(auth_tokens, "admin"))
    assert resp.status_code == 404


def test_modify_card_points_unauthenticated(client):
    resp = client.patch(BASE_URL + f"/customers/cards/1?points={100}")
    assert resp.status_code == 401
