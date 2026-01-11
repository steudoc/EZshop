import pytest
from utils_route import BASE_URL, auth_header, create_product, create_open_sale, create_pending_sale_with_items, create_paid_sale_with_items, add_item_to_sale

# -----------------------------------------------------------------------------
# TESTS FOR PATCH /sales/{sale_id}/items/{product_barcode}/discount
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Apply Product Discount Successfully
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - product_barcode type: String, Value: Valid
#   - discount_rate type: Float, Value: >=0 && <1
#   - Sale presence: Yes
#   - Sale status: OPEN
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("discount", [0.1, 0.5, 0.99, 0.0])
def test_1_apply_product_discount_success(client, auth_tokens, role, discount):
    """
    Test 1: Verify that authorized users can apply a valid discount rate to a specific product in an OPEN sale.
    """
    # Setup: Create Product
    barcode = create_product(client, auth_tokens)
    
    # Setup: Create Sale and Add Item
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode)

    # Action: Apply discount to the product line
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate={discount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status 200 OK and Success Boolean
    assert response.status_code == 200
    assert response.json()["success"] is True

# -----------------------------------------------------------------------------
# TEST 2: Invalid Discount Rate Value (>= 1)
# Partitions covered:
#   - discount_rate value: >=1 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_discount", [1.0, 1.5, 10.0])
def test_2_apply_product_discount_invalid_value_high(client, auth_tokens, role, invalid_discount):
    """
    Test 2: Verify error when discount rate is >= 1.0.
    """
    # Setup
    barcode = create_product(client, auth_tokens)
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode)

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate={invalid_discount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 3: Invalid Discount Rate Value (< 0)
# Partitions covered:
#   - discount_rate value: <0 (Implied invalid range) --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_3_apply_product_discount_invalid_value_negative(client, auth_tokens, role):
    """
    Test 3: Verify error when discount rate is negative.
    """
    # Setup
    barcode = create_product(client, auth_tokens)
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode)
    
    invalid_discount = -0.5

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate={invalid_discount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 4: Invalid Sale ID Value (<= 0)
# Partitions covered:
#   - sale_id value: <=0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
@pytest.mark.parametrize("invalid_id", [0, -5])
def test_4_apply_product_discount_invalid_sale_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 4: Verify error when sale_id is non-positive.
    """
    barcode = create_product(client, auth_tokens)

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{invalid_id}/items/{barcode}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 5: Invalid Barcode Format
# Partitions covered:
#   - product_barcode value: Not valid --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
@pytest.mark.parametrize("invalid_barcode", ["abc", "123", "short"])
def test_5_apply_product_discount_invalid_barcode_format(client, auth_tokens, role, invalid_barcode):
    """
    Test 5: Verify error when product_barcode has invalid format.
    """
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{invalid_barcode}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 6: Sale Not Found
# Partitions covered:
#   - Sale presence: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_6_apply_product_discount_sale_not_found(client, auth_tokens, role):
    """
    Test 6: Verify error when sale ID is valid but sale does not exist.
    """
    barcode = create_product(client, auth_tokens)
    non_existent_id = 999999
    
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{non_existent_id}/items/{barcode}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"

# -----------------------------------------------------------------------------
# TEST 7: Sale Exists but Product Not in Sale
# Partitions covered:
#   - Product in sale: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_7_apply_product_discount_line_not_found(client, auth_tokens, role):
    """
    Test 7: Verify error when Sale exists, but the specified product is not part of the sale.
    """
    # Setup: Create Sale but DO NOT add item
    sale_id = create_open_sale(client, auth_tokens[role])
    barcode = create_product(client, auth_tokens)

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate=0.5",
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
def test_8_apply_product_discount_state_pending(client, auth_tokens, role):
    """
    Test 8: Verify that product discount cannot be applied to a PENDING sale.
    """
    # Setup: Create PENDING sale with item
    barcode = create_product(client, auth_tokens)
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode,1)])

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate=0.5",
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
def test_9_apply_product_discount_state_paid(client, auth_tokens, role):
    """
    Test 9: Verify that product discount cannot be applied to a PAID sale.
    """
    # Setup: Create PAID sale with item
    barcode = create_product(client, auth_tokens)
    sale_id = create_paid_sale_with_items(client, auth_tokens, role, items=[(barcode,1)])

    # Action
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"

# -----------------------------------------------------------------------------
# TEST 10: Invalid Sale ID Type
# Partitions covered:
#   - sale_id type: String --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_10_apply_product_discount_invalid_sale_id_type(client, auth_tokens, role):
    """
    Test 10: Verify error when sale_id has wrong type (String).
    """
    barcode = create_product(client, auth_tokens)

    # Action: Call with invalid string for sale_id
    response = client.patch(
        f"{BASE_URL}/sales/invalid_string_id/items/{barcode}/discount?discount_rate=0.5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# TEST 11: Invalid Discount Rate Type
# Partitions covered:
#   - discount_rate type: String --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_11_apply_product_discount_invalid_discount_rate_type(client, auth_tokens, role):
    """
    Test 11: Verify error when discount_rate has wrong type (String).
    We use a valid sale ID setup for this to isolate the discount_rate error.
    """
    # Setup: Create a sale to ensure the error is strictly about the discount_rate parameter
    sale_id = create_open_sale(client, auth_tokens[role])
    barcode = create_product(client, auth_tokens)

    # Action: Call with invalid string for discount_rate
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/items/{barcode}/discount?discount_rate=invalid_string",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# TEST 12: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_12_apply_product_discount_unauthenticated(client):
    """
    Test 12: Verify unauthenticated users cannot apply a discount.
    """
    # Action
    response = client.patch(
        f"{BASE_URL}/sales/1/items/123456789012/discount?discount_rate=0.5"
    )

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"