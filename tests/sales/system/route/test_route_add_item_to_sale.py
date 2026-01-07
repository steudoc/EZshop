import pytest
from utils_route import BASE_URL, auth_header, create_product, create_open_sale, get_product, close_sale, pay_sale

# -----------------------------------------------------------------------------
# TESTS FOR POST /sales/{sale_id}/items
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Add Item Successfully
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - barcode type: String, Value: Valid
#   - amount type: Int, Value: >0 && <=Q (Quantity available)
#   - Sale presence: Yes
#   - Product presence: Yes
#   - Sale status: OPEN
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_add_item_success(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can add an item to an open sale.
    Also verifies Functional Requirement: The quantity is deducted from the shelf.
    """
    # Setup
    barcode = create_product(client, auth_tokens, quantity=50)
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action: Add 10 items
    amount_to_add = 10
    response = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount={amount_to_add}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 201
    assert response.json()["success"] is True

    # Assertion: inventory reduced
    # 50 - 10 = 40
    new_qty = get_product(client, auth_tokens, barcode)["quantity"]
    assert new_qty == 40


# -----------------------------------------------------------------------------
# TEST 2: Amount Exceeds Quantity
# Partitions covered:
#   - amount value: >Q (Quantity available) --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_add_item_insufficient_stock(client, auth_tokens, role):
    """
    Test 2: Verify error when requested amount is greater than available quantity.
    """
    # Setup: Product Qty = 5
    barcode = create_product(client, auth_tokens, quantity=5)
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action: Try to add 10 items
    response = client.post(
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
@pytest.mark.parametrize("invalid_amount", [0, -5])
def test_3_add_item_invalid_amount_value(client, auth_tokens, role, invalid_amount):
    """
    Test 3: Verify error when amount is zero or negative.
    """
    # Setup
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action
    response = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount={invalid_amount}",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 4: Invalid Barcode Format
# Partitions covered:
#   - barcode value: Not valid (digits checks) --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_barcode", ["abc", "123", ""])
def test_4_add_item_invalid_barcode_format(client, auth_tokens, role, invalid_barcode):
    """
    Test 4: Verify error when barcode string does not meet valid format (12-14 digits).
    """
    sale_id = create_open_sale(client, auth_tokens[role])

    # Action
    response = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={invalid_barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 5: Product Not Found
# Partitions covered:
#   - Product presence: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_5_add_item_product_not_found(client, auth_tokens, role):
    """
    Test 5: Verify error when barcode is valid format but product does not exist.
    """
    sale_id = create_open_sale(client, auth_tokens[role])
    non_existent_barcode = "123456789012"

    # Action
    response = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={non_existent_barcode}&amount=1",
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
def test_6_add_item_sale_not_found(client, auth_tokens, role):
    """
    Test 6: Verify error when sale ID is valid int but does not exist.
    """
    barcode = create_product(client, auth_tokens)
    non_existent_sale_id = 99999

    # Action
    response = client.post(
        f"{BASE_URL}/sales/{non_existent_sale_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"


# -----------------------------------------------------------------------------
# TEST 7: Invalid Sale ID Value (<=0)
# Partitions covered:
#   - sale_id value: <=0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", [0, -1])
def test_7_add_item_invalid_sale_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 7: Verify error when sale ID is not positive.
    """
    barcode = create_product(client, auth_tokens)

    # Action
    response = client.post(
        f"{BASE_URL}/sales/{invalid_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"


# -----------------------------------------------------------------------------
# TEST 8: Invalid Sale Status (PENDING or PAID)
# Partitions covered:
#   - Sale status: PENDING --> InvalidStateError, 420
#   - Sale status: PAID --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_8_add_item_invalid_state_pending(client, auth_tokens, role):
    """
    Test 8a: Verify error when adding item to a PENDING sale.
    """
    # Setup
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Add an item initially to allow closing
    resp_1 = client.post(f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1", 
                headers=auth_header(auth_tokens, role))
    assert resp_1.status_code == 201
    
    # Close the sale (Status -> PENDING)
    close_sale(client, auth_tokens[role], sale_id)

    # Action: Try to add another item
    resp_2 = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert resp_2.status_code == 420
    assert resp_2.json()["name"] == "InvalidStateError"

@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_8b_add_item_invalid_state_paid(client, auth_tokens, role):
    """
    Test 8b: Verify error when adding item to a PAID sale.
    """
    # Setup
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Add item, Close, Pay (Status -> PAID)
    # Cost: 1 unit * 10.0 = 10.0
    resp_1 = client.post(f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1", 
                headers=auth_header(auth_tokens, role))
    assert resp_1.status_code == 201

    close_sale(client, auth_tokens[role], sale_id)
    pay_sale(client, auth_tokens[role], sale_id, 10.0)

    # Action: Try to add another item
    resp_2 = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert resp_2.status_code == 420
    assert resp_2.json()["name"] == "InvalidStateError"


# -----------------------------------------------------------------------------
# TEST 9: Invalid Data Types
# Partitions covered:
#   - sale_id type: String/Float --> Unprocessable Entity, 422
#   - amount type: String/Float --> Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin"])
def test_9_add_item_invalid_types(client, auth_tokens, role):
    """
    Test 9: Verify errors when parameters have wrong types.
    """
    barcode = create_product(client, auth_tokens)
    sale_id = create_open_sale(client, auth_tokens[role])

    # Case A: Sale ID is string
    resp_1 = client.post(
        f"{BASE_URL}/sales/invalid_id_string/items?barcode={barcode}&amount=1",
        headers=auth_header(auth_tokens, role)
    )
    assert resp_1.status_code == 422

    # Case B: Amount is string
    resp_2 = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount=ten",
        headers=auth_header(auth_tokens, role)
    )
    assert resp_2.status_code == 422


# -----------------------------------------------------------------------------
# TEST 10: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_10_add_item_unauthenticated(client):
    """
    Test 10: Verify unauthenticated access is rejected.
    """
    # Action (Parameters are valid, but no auth)
    response = client.post(
        f"{BASE_URL}/sales/1/items?barcode=123456789012&amount=1"
    )

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"


# -----------------------------------------------------------------------------
# TEST 11: Verify Item Persistence
# Partitions covered:
#   - Functional Requirement: Verify item is actually added to the sale lines
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_11_add_item_verify_persistence(client, auth_tokens, role):
    """
    Test 11: Verify that after adding an item, it actually appears in the sale's line items.
    """
    # Setup
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_open_sale(client, auth_tokens[role])
    amount_to_add = 1

    # Action: Add item
    response = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount={amount_to_add}",
        headers=auth_header(auth_tokens, role)
    )
    assert response.status_code == 201

    # Verification: Fetch the sale to check lines
    get_response = client.get(
        f"{BASE_URL}/sales/{sale_id}",
        headers=auth_header(auth_tokens, role)
    )
    assert get_response.status_code == 200
    
    sale_data = get_response.json()
    
    # Check that lines is not empty
    assert "lines" in sale_data
    assert len(sale_data["lines"]) > 0
    
    # Check specific details of the added item
    added_item = sale_data["lines"][0]    
    assert added_item["product_barcode"] == barcode 
    assert added_item["quantity"] == amount_to_add