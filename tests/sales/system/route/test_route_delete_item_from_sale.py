import pytest
from utils_route import BASE_URL, auth_header, create_product, add_item_to_sale, create_open_sale, get_product, create_pending_sale_with_items, create_paid_sale_with_items

# -----------------------------------------------------------------------------
# TESTS FOR DELETE /sales/{sale_id}/items
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Remove Item Successfully
# Partitions covered:
#   - User type: Administrator, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - barcode type: String, Value: Valid
#   - amount type: Int, Value: >0 && <=T (Quantity in sale)
#   - Sale presence: Yes
#   - Product presence: Yes
#   - Sale status: OPEN
# Expected: 202 Accepted
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_delete_item_success(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can remove items from an OPEN sale.
    """
    # Setup: Create Product (Stock=100)
    barcode = create_product(client, auth_tokens, quantity=100)
    
    # Setup: Create Sale and Add 10 items (Stock becomes 90)
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode, amount=10)
    
    assert get_product(client, auth_tokens, barcode)["quantity"] == 90

    # Action: Remove 5 items
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=5",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status check
    assert response.status_code == 202
    assert response.json()["success"] is True

    # Assertion: Verify Inventory Restored (90 + 5 = 95)
    new_qty = get_product(client, auth_tokens, barcode)["quantity"]
    assert new_qty == 95


# -----------------------------------------------------------------------------
# TEST 2: Amount Value > T (Quantity in Sale)
# Partitions covered:
#   - amount value: >T (Quantity of product initially added) --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_delete_item_invalid_amount_greater_than_sale(client, auth_tokens, role):
    """
    Test 2: Verify error when trying to remove more items than exist in the sale line.
    """
    # Setup: Sale with 5 items
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode, amount=5)

    # Action: Try to remove 10 items
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=10",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 3: Invalid Amount Value (<= 0)
# Partitions covered:
#   - amount value: <=0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_amount", [0, -1, -50])
def test_3_delete_item_invalid_amount_value(client, auth_tokens, role, invalid_amount):
    """
    Test 3: Verify error when amount to remove is zero or negative.
    """
    # Setup
    barcode = create_product(client, auth_tokens)
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode, amount=5)

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount={invalid_amount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 4: Invalid Barcode Value
# Partitions covered:
#   - barcode value: Not valid --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_barcode", ["abc", "123", ""])
def test_4_delete_item_invalid_barcode_format(client, auth_tokens, role, invalid_barcode):
    """
    Test 4: Verify error when barcode string does not meet digits requirements.
    """
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={invalid_barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 5: Product Not In Sale
# Partitions covered:
#   - Product presence: No (in sale) --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_5_delete_item_product_not_in_sale(client, auth_tokens, role):
    """
    Test 5: Verify error when attempting to remove a product that is not in the sale.
    """
    # Setup: Sale exists, Product exists, but Product NOT added to sale
    sale_id = create_open_sale(client, auth_tokens[role])
    barcode = create_product(client, auth_tokens)

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"


# -----------------------------------------------------------------------------
# TEST 6: Sale Not Found
# Partitions covered:
#   - Sale presence: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_6_delete_item_sale_not_found(client, auth_tokens, role):
    """
    Test 6: Verify error when sale ID is valid but sale does not exist.
    """
    barcode = create_product(client, auth_tokens)
    non_existent_id = 999999

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{non_existent_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"


# -----------------------------------------------------------------------------
# TEST 7: Invalid Sale ID Value (<= 0)
# Partitions covered:
#   - sale_id value: <=0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", [0, -5])
def test_7_delete_item_invalid_sale_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 7: Verify error when sale_id is non-positive.
    """
    barcode = create_product(client, auth_tokens)

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{invalid_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 8: Sale Status Invalid (PENDING)
# Partitions covered:
#   - Sale status: PENDING --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_8_delete_item_invalid_state_pending(client, auth_tokens, role):
    """
    Test 8: Verify that items cannot be removed from a PENDING sale.
    """
    # Setup: PENDING sale
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode, 10)])

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1",
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
def test_9_delete_item_invalid_state_paid(client, auth_tokens, role):
    """
    Test 9: Verify that items cannot be removed from a PAID sale.
    """
    # Setup: PAID sale
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_paid_sale_with_items(client, auth_tokens, role, items=[(barcode, 10)])

    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"


# -----------------------------------------------------------------------------
# TEST 10: Invalid Data Types
# Partitions covered:
#   - sale_id type: String --> Unprocessable Entity, 422
#   - amount type: String --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_10_delete_item_invalid_types(client, auth_tokens, role):
    """
    Test 10: Verify errors when parameters have wrong types.
    """
    barcode = create_product(client, auth_tokens)
    
    # Case A: Sale ID is String
    resp_1 = client.delete(
        f"{BASE_URL}/sales/invalid_id/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )
    assert resp_1.status_code == 422

    # Case B: Amount is String
    sale_id = create_open_sale(client, auth_tokens[role])
    resp_2 = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=one",
        headers=auth_header(auth_tokens, role)
    )
    assert resp_2.status_code == 422


# -----------------------------------------------------------------------------
# TEST 11: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_11_delete_item_unauthenticated(client):
    """
    Test 11: Verify unauthenticated users cannot remove items.
    """
    # Action
    response = client.delete(
        f"{BASE_URL}/sales/1/items?barcode=123456789012&amount=1"
    )

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"

# -----------------------------------------------------------------------------
# TEST 12: Missing Parameters
# Partitions covered:
#   - amount type: Not present --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_12_delete_item_missing_amount(client, auth_tokens, role):
    """
    Test 12: Verify error when amount parameter is missing.
    """
    sale_id = create_open_sale(client, auth_tokens[role])
    barcode = create_product(client, auth_tokens)
    
    # Action: Call without amount
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# TEST 13: Completely Remove an Item
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_13_delete_item_completely(client, auth_tokens, role):
    """
    Test 13: Completely remove an item to see if it is also removed from the line
    """
    # Setup: Create Product (Stock=100)
    barcode = create_product(client, auth_tokens, quantity=100)
    
    # Setup: Create Sale and Add 10 items (Stock becomes 90)
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode, amount=10)
    
    assert get_product(client, auth_tokens, barcode)["quantity"] == 90

    # Action: Remove all 10 items
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=10",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Status check
    assert response.status_code == 202
    assert response.json()["success"] is True

    # Assertion: Verify Inventory Restored (90 + 10 = 100)
    new_qty = get_product(client, auth_tokens, barcode)["quantity"]
    assert new_qty == 100

    # Verification
    get_response = client.get(
        f"{BASE_URL}/sales/{sale_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert get_response.status_code == 200
    
    sale_data = get_response.json()
    
    # Check that lines is empty
    assert "lines" in sale_data
    assert len(sale_data["lines"]) == 0

    