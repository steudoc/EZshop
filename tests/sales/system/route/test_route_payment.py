import pytest
from utils_route import BASE_URL, auth_header, get_system_balance, create_product, create_pending_sale_with_items, create_open_sale, add_item_to_sale

# -----------------------------------------------------------------------------
# TESTS FOR PATCH /sales/{sale_id}/pay
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Pay Sale Successfully
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - cash_amount type: Float, Value: >= C (Cost)
#   - Sale presence: Yes
#   - Sale status: PENDING
#   - Expected: 200 OK, Balance updated, Status -> PAID
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_pay_sale_success(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can pay a PENDING sale.
    """
    # Setup: Product Price=10.0, Sale Qty=2 -> Total Cost=20.0
    barcode = create_product(client, auth_tokens, price_per_unit=10.0)
    sale_id, total_cost = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode, 2)])
    
    # Initial Balance (Should be 0 after reset)
    initial_balance = get_system_balance(client, auth_tokens)

    # Action: Pay with 25.0 (Change should be 5.0)
    cash_paid = 25.0
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount={cash_paid}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status and Change
    assert response.status_code == 200
    # Expected change: 25.0 - 20.0 = 5.0
    assert response.json()["change"] == 5.0

    # Assertion: Verify Sale Status is PAID
    resp_get = client.get(f"{BASE_URL}/sales/{sale_id}", headers=auth_header(auth_tokens, role))
    assert resp_get.json()["status"] == "PAID"

    # Assertion: Verify Balance Updated
    # Balance should increase by Total Cost (20.0)
    new_balance = get_system_balance(client, auth_tokens)
    assert new_balance == initial_balance + total_cost


# -----------------------------------------------------------------------------
# TEST 2: Insufficient Cash (Value < Cost)
# Partitions covered:
#   - cash_amount value: < C --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_pay_sale_insufficient_cash(client, auth_tokens, role):
    """
    Test 2: Verify error when cash amount is less than total sale cost.
    """
    # Setup: Cost = 20.0
    barcode = create_product(client, auth_tokens, price_per_unit=10.0)
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode, 2)])

    # Action: Pay with 15.0
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount=15.0",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 3: Invalid Cash Amount Value (<= 0)
# Partitions covered:
#   - cash_amount value: <= 0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_amount", [0.0, -10.0])
def test_3_pay_sale_invalid_amount_value(client, auth_tokens, role, invalid_amount):
    """
    Test 3: Verify error when cash amount is zero or negative.
    """
    # Setup
    barcode = create_product(client, auth_tokens)
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode, 1)])

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount={invalid_amount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 4: Invalid Cash Amount Type (String)
# Partitions covered:
#   - cash_amount type: String --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_4_pay_sale_invalid_amount_type_string(client, auth_tokens, role):
    """
    Test 4: Verify error when cash_amount is a non-numeric string.
    """
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount=abc",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# TEST 5: Invalid Sale ID Value (<= 0)
# Partitions covered:
#   - sale_id value: <= 0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", [0, -5])
def test_5_pay_sale_invalid_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 5: Verify error when sale_id is non-positive.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{invalid_id}/pay?cash_amount=100.0",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 6: Invalid Sale ID Type (String)
# Partitions covered:
#   - sale_id type: String --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_6_pay_sale_invalid_id_type(client, auth_tokens, role):
    """
    Test 6: Verify error when sale_id is not an integer.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/abc/pay?cash_amount=100.0",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# TEST 7: Sale Not Found
# Partitions covered:
#   - Sale presence: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_7_pay_sale_not_found(client, auth_tokens, role):
    """
    Test 7: Verify error when sale ID is valid but sale does not exist.
    """
    non_existent_id = 999999

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{non_existent_id}/pay?cash_amount=100.0",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"


# -----------------------------------------------------------------------------
# TEST 8: Invalid State - OPEN
# Partitions covered:
#   - Sale status: OPEN --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_8_pay_sale_invalid_state_open(client, auth_tokens, role):
    """
    Test 8: Verify that an OPEN sale cannot be paid directly (must be closed/PENDING first).
    """
    # Setup: Create OPEN sale
    barcode = create_product(client, auth_tokens)
    
    # Create Sale and Add Item, but DO NOT close
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode)

    # Action: Try to pay
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount=100.0",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"


# -----------------------------------------------------------------------------
# TEST 9: Invalid State - PAID
# Partitions covered:
#   - Sale status: PAID --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_9_pay_sale_invalid_state_paid(client, auth_tokens, role):
    """
    Test 9: Verify that a PAID sale cannot be paid again.
    """
    # Setup: Create a PAID sale
    barcode = create_product(client, auth_tokens, price_per_unit=10.0)
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode, 1)])
    
    # Pay it once (Success)
    resp_1 = client.patch(f"{BASE_URL}/sales/{sale_id}/pay?cash_amount=10.0", headers=auth_header(auth_tokens, role))
    assert resp_1.status_code == 200

    # Action: Try to pay again
    resp_2 = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount=10.0",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert resp_2.status_code == 420
    assert resp_2.json()["name"] == "InvalidStateError"


# -----------------------------------------------------------------------------
# TEST 10: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_10_pay_sale_unauthenticated(client):
    """
    Test 10: Verify unauthenticated users cannot pay a sale.
    """
    # Action
    response = client.patch(f"{BASE_URL}/sales/1/pay?cash_amount=100.0")

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"