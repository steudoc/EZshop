import pytest
from utils_route import BASE_URL, auth_header, create_open_sale, create_product, create_pending_sale_with_items, get_product, create_paid_sale_with_items

# -----------------------------------------------------------------------------
# TESTS FOR DELETE /sales/{sale_id}
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Delete OPEN Sale
# Partition covered:
#   - User type: Administrator, ShopManager, Cashier
#   - Sale ID: Valid Int (>0)
#   - Sale Status: OPEN
#   - Expected: 204 No Content
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_delete_sale_success_open(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can delete an OPEN sale.
    """
    # Setup: Create an OPEN sale
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Action: Delete the sale
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion: Status Code
    assert response.status_code == 204
    
    # Verify Deletion: Get sale should return 404
    resp_get = client.get(f"{BASE_URL}/sales/{sale_id}", headers=auth_header(auth_tokens, role))
    assert resp_get.status_code == 404

# -----------------------------------------------------------------------------
# TEST 2: Delete PENDING Sale (and Restock Inventory)
# Partition covered:
#   - User type: Administrator, ShopManager, Cashier
#   - Sale ID: Valid Int (>0)
#   - Sale Status: PENDING
#   - Expected: 204 No Content
#   - Side Effect: Product quantity restored
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_delete_sale_success_pending(client, auth_tokens, role):
    """
    Test 2: Verify that authorized users can delete a PENDING sale.
    Also verify that items in the sale are returned to the inventory.
    """
    # Setup: Create Product (Qty=100)
    barcode = create_product(client, auth_tokens, quantity=100)
    
    # Setup: Create PENDING sale with 10 items (Stock becomes 90)
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role, items=[(barcode, 10)])
    
    # Verify stock is 90
    assert get_product(client, auth_tokens, barcode)["quantity"] == 90
    
    # Action: Delete the PENDING sale
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion: Status Code
    assert response.status_code == 204
    
    # Assertion: Verify Sale is gone
    resp_get = client.get(f"{BASE_URL}/sales/{sale_id}", headers=auth_header(auth_tokens, role))
    assert resp_get.status_code == 404
    
    # Assertion: Verify Stock is restored to 100
    assert get_product(client, auth_tokens, barcode)["quantity"] == 100

# -----------------------------------------------------------------------------
# TEST 3: Delete Sale - Invalid ID Type
# Partition covered:
#   - User type: Administrator (Representative)
#   - Sale ID Type: String, Float
#   - Expected: Unprocessable Entity, 422
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", ["invalid_string", 1.5, "123abc"])
def test_3_delete_sale_invalid_type(client, auth_tokens, role, invalid_id):
    """
    Test 3: Verify error when sale_id is not an integer.
    """
    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{invalid_id}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# TEST 4: Delete Sale - Invalid ID Value
# Partition covered:
#   - User type: Administrator (Representative)
#   - Sale ID Value: <= 0
#   - Expected: 400 BadRequest
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_value", [0, -1, -50])
def test_4_delete_sale_invalid_value(client, auth_tokens, role, invalid_value):
    """
    Test 4: Verify error when sale_id is <= 0.
    """
    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{invalid_value}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 5: Delete Sale - Not Found
# Partition covered:
#   - User type: Administrator (Representative)
#   - Sale ID: Valid Int (>0)
#   - Sale Presence: No
#   - Expected: 404 NotFound
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_5_delete_sale_not_found(client, auth_tokens, role):
    """
    Test 5: Verify error when sale does not exist.
    """
    non_existent_id = 999999
    
    # Action
    response = client.delete(
        f"{BASE_URL}/sales/{non_existent_id}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"

# -----------------------------------------------------------------------------
# TEST 6: Delete Sale - Invalid State (PAID)
# Partition covered:
#   - User type: Administrator (Representative)
#   - Sale Status: PAID
#   - Expected: 420 InvalidStateError
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_6_delete_sale_invalid_state_paid(client, auth_tokens, role):
    """
    Test 6: Verify that a PAID sale cannot be deleted.
    """
    # Setup: Create a PAID sale
    barcode = create_product(client, auth_tokens, quantity=100)
    sale_id = create_paid_sale_with_items(client, auth_tokens, role, items=[(barcode, 5)])
    
    # Action: Try to delete PAID sale
    response = client.delete(
        f"{BASE_URL}/sales/{sale_id}",
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 420, f"Expected 420, got {response.status_code}. Body: {response.text}"
    assert response.json()["name"] == "InvalidStateError"
    
    # Verify Sale still exists
    resp_get = client.get(f"{BASE_URL}/sales/{sale_id}", headers=auth_header(auth_tokens, role))
    assert resp_get.status_code == 200

# -----------------------------------------------------------------------------
# TEST 7: Delete Sale - Unauthenticated
# Partition covered:
#   - User type: Unauthenticated
#   - Expected: 401 Unauthorized
# -----------------------------------------------------------------------------
def test_7_delete_sale_unauthenticated(client):
    """
    Test 7: Verify that unauthenticated users cannot delete a sale.
    """    
    # Action
    response = client.delete(f"{BASE_URL}/sales/1")
    
    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"