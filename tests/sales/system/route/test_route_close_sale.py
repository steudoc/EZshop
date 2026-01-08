import pytest
from utils_route import BASE_URL, auth_header, create_product, create_open_sale, add_item_to_sale, create_pending_sale_with_items, create_paid_sale_with_items

# -----------------------------------------------------------------------------
# TESTS FOR PATCH /sales/{sale_id}/close
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Close Non-Empty Sale (OPEN -> PENDING)
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - Sale presence: Yes
#   - Sale status: OPEN
#   - Empty OPEN sale: No
#   - Expected Result: 200 OK, Status changes to PENDING
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_close_sale_success_non_empty(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can close a non-empty OPEN sale.
    The sale status should change to PENDING.
    """
    # Setup: Create Sale and Add Item (Non-empty)
    barcode = create_product(client, auth_tokens)
    
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode, amount=1)

    # Action: Close the sale
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status Code
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify Status Change
    resp_get = client.get(f"{BASE_URL}/sales/{sale_id}", headers=auth_header(auth_tokens, role))
    assert resp_get.status_code == 200
    assert resp_get.json()["status"] == "PENDING"

# -----------------------------------------------------------------------------
# TEST 2: Close Empty Sale (OPEN -> DELETED)
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - Sale presence: Yes
#   - Sale status: OPEN
#   - Empty OPEN sale: Yes
#   - Expected Result: 200 OK, Sale is DELETED
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_close_sale_success_empty(client, auth_tokens, role):
    """
    Test 2: Verify that authorized users can close an EMPTY OPEN sale.
    According to requirements, closing an empty sale should DELETE it from the database.
    """
    # Setup: Create Sale but DO NOT add items
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action: Close the sale
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status Code
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify Sale is Deleted (Get returns 404)
    resp_get = client.get(f"{BASE_URL}/sales/{sale_id}", headers=auth_header(auth_tokens, role))
    assert resp_get.status_code == 404

# -----------------------------------------------------------------------------
# TEST 3: Invalid Sale ID Value (<= 0)
# Partitions covered:
#   - sale_id value: <=0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", [0, -1, -50])
def test_3_close_sale_invalid_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 3: Verify error when sale_id is non-positive.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{invalid_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 4: Invalid Sale ID Type (String/Float)
# Partitions covered:
#   - sale_id type: String --> Unprocessable Entity, 422
#   - sale_id type: Float --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
@pytest.mark.parametrize("invalid_id", ["abc", 1.5])
def test_4_close_sale_invalid_id_type(client, auth_tokens, role, invalid_id):
    """
    Test 4: Verify error when sale_id is not an integer.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{invalid_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# TEST 5: Sale Not Found
# Partitions covered:
#   - Sale presence: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_5_close_sale_not_found(client, auth_tokens, role):
    """
    Test 5: Verify error when sale ID is valid but sale does not exist.
    """
    non_existent_id = 999999

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{non_existent_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"

# -----------------------------------------------------------------------------
# TEST 6: Invalid Sale Status (PENDING)
# Partitions covered:
#   - Sale status: PENDING --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_6_close_sale_invalid_state_pending(client, auth_tokens, role):
    """
    Test 6: Verify that a PENDING sale cannot be closed again.
    """
    # Setup: Create PENDING sale
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role)

    # Action: Try to close again
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"

# -----------------------------------------------------------------------------
# TEST 7: Invalid Sale Status (PAID)
# Partitions covered:
#   - Sale status: PAID --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_7_close_sale_invalid_state_paid(client, auth_tokens, role):
    """
    Test 7: Verify that a PAID sale cannot be closed.
    """
    # Setup: Create PAID sale
    sale_id = create_paid_sale_with_items(client, auth_tokens, role)

    # Action: Try to close
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/close",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"

# -----------------------------------------------------------------------------
# TEST 8: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_8_close_sale_unauthenticated(client):
    """
    Test 8: Verify unauthenticated users cannot close a sale.
    """
    # Action
    response = client.patch(f"{BASE_URL}/sales/1/close")

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"