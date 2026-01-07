import pytest
from utils_route import BASE_URL, auth_header, create_open_sale, create_pending_sale_with_items, create_paid_sale_with_items

# -----------------------------------------------------------------------------
# TESTS FOR PATCH /sales/{sale_id}/discount
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Apply Discount Successfully
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - discount_rate type: Float, Value: >=0 && <1
#   - Sale presence: Yes
#   - Sale status: OPEN
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("discount", [0.1, 0.5, 0.99])
def test_1_apply_discount_success(client, auth_tokens, role, discount):
    """
    Test 1: Verify that authorized users can apply a valid discount rate to an OPEN sale.
    """
    # Setup: Create an OPEN sale
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Action: Apply discount
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/discount?discount_rate={discount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status 200 OK and Success Boolean
    assert response.status_code == 200, f"{response.text}"
    assert response.json()["success"] is True

# -----------------------------------------------------------------------------
# TEST 2: Invalid Discount Rate Value (>= 1)
# Partitions covered:
#   - discount_rate value: >=1 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_discount", [1.0, 1.5, 2.0])
def test_2_apply_discount_invalid_value_high(client, auth_tokens, role, invalid_discount):
    """
    Test 2: Verify error when discount rate is >= 1.0.
    """
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/discount?discount_rate={invalid_discount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 3: Invalid Discount Rate Value (< 0)
# Partitions covered:
#   - discount_rate value: <0 (Implied by valid range >=0 && <1)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_3_apply_discount_invalid_value_negative(client, auth_tokens, role):
    """
    Test 3: Verify error when discount rate is negative.
    """
    sale_id = create_open_sale(client, auth_tokens[role])
    invalid_discount = -0.1

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/discount?discount_rate={invalid_discount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 4: Invalid Discount Rate Type (String)
# Partitions covered:
#   - discount_rate type: String --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_4_apply_discount_invalid_type_string(client, auth_tokens, role):
    """
    Test 4: Verify error when discount_rate is not a number.
    """
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/discount?discount_rate=abc",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# TEST 5: Invalid Sale ID Value (<= 0)
# Partitions covered:
#   - sale_id value: <=0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
@pytest.mark.parametrize("invalid_id", [0, -5])
def test_5_apply_discount_invalid_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 5: Verify error when sale_id is non-positive.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{invalid_id}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 6: Invalid Sale ID Type (String/Float)
# Partitions covered:
#   - sale_id type: String --> Unprocessable Entity, 422
#   - sale_id type: Float --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
@pytest.mark.parametrize("invalid_id", ["abc", 1.5])
def test_6_apply_discount_invalid_id_type(client, auth_tokens, role, invalid_id):
    """
    Test 6: Verify error when sale_id is not an integer.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{invalid_id}/discount?discount_rate=0.5",
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
def test_7_apply_discount_sale_not_found(client, auth_tokens, role):
    """
    Test 7: Verify error when sale ID is valid but sale does not exist.
    """
    non_existent_id = 999999
    
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{non_existent_id}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"

# -----------------------------------------------------------------------------
# TEST 8: Sale Status Invalid (PENDING)
# Partitions covered:
#   - Sale status: PENDING --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_8_apply_discount_invalid_state_pending(client, auth_tokens, role):
    """
    Test 8: Verify that discount cannot be applied to a PENDING sale.
    """
    # Setup: Create PENDING sale
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role)

    # Action: Try to apply discount
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"

# -----------------------------------------------------------------------------
# TEST 9: Sale Status Invalid (PAID)
# Partitions covered:
#   - Sale status: PAID --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_9_apply_discount_invalid_state_paid(client, auth_tokens, role):
    """
    Test 9: Verify that discount cannot be applied to a PAID sale.
    """
    # Setup: Create PAID sale
    sale_id = create_paid_sale_with_items(client, auth_tokens, role)

    # Action: Try to apply discount
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"

# -----------------------------------------------------------------------------
# TEST 10: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_10_apply_discount_unauthenticated(client):
    """
    Test 10: Verify unauthenticated users cannot apply a discount.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/1/discount?discount_rate=0.5"
    )

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"