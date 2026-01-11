import pytest
from utils_route import BASE_URL, auth_header, create_product, create_paid_sale_with_items, create_pending_sale_with_items, create_open_sale, add_item_to_sale

# -----------------------------------------------------------------------------
# TESTS FOR GET /sales/{sale_id}/points
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Get Points for PAID Sale
# Partitions covered:
#   - User type: Admin, ShopManager, Cashier
#   - sale_id type: Int, Value: >0
#   - Sale presence: Yes
#   - Sale status: PAID
#   - Expected: 200 OK, Points calculated correctly (Total / 10)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_get_sale_points_success(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can get points for a PAID sale.
    Calculation check: 2 items * 50.0 = 100.0 Total. Points = 100 / 10 = 10.
    """
    # Setup: Create Product (Price=50.0)
    barcode = create_product(client, auth_tokens, price_per_unit=50.0)
    
    # Setup: Create PAID sale with 2 items
    sale_id = create_paid_sale_with_items(client, auth_tokens, role, items=[(barcode, 2)])
    
    # Action: Get Points
    response = client.get(
        f"{BASE_URL}/sales/{sale_id}/points",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    # Points logic: (N * UnitPrice) / 10 = (2 * 50) / 10 = 10
    assert data["points"] == 10


# -----------------------------------------------------------------------------
# TEST 2: Invalid Sale Status - OPEN
# Partitions covered:
#   - Sale status: OPEN --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_get_sale_points_invalid_state_open(client, auth_tokens, role):
    """
    Test 2: Verify error when requesting points for an OPEN sale.
    """
    # Setup: Create OPEN sale
    barcode = create_product(client, auth_tokens)
    
    # Create Sale, Add item, but DO NOT Close/Pay
    sale_id = create_open_sale(client, auth_tokens[role])
    add_item_to_sale(client, auth_tokens[role], sale_id, barcode)
    
    # Action
    response = client.get(
        f"{BASE_URL}/sales/{sale_id}/points",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"


# -----------------------------------------------------------------------------
# TEST 3: Invalid Sale Status - PENDING
# Partitions covered:
#   - Sale status: PENDING --> InvalidStateError, 420
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_3_get_sale_points_invalid_state_pending(client, auth_tokens, role):
    """
    Test 3: Verify error when requesting points for a PENDING sale.
    """
    # Setup: Create PENDING sale
    sale_id, _ = create_pending_sale_with_items(client, auth_tokens, role)

    # Action
    response = client.get(
        f"{BASE_URL}/sales/{sale_id}/points",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 420
    assert response.json()["name"] == "InvalidStateError"


# -----------------------------------------------------------------------------
# TEST 4: Sale Not Found
# Partitions covered:
#   - Sale presence: No --> NotFoundError, 404
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_4_get_sale_points_not_found(client, auth_tokens, role):
    """
    Test 4: Verify error when sale ID does not exist.
    """
    non_existent_id = 999999

    # Action
    response = client.get(
        f"{BASE_URL}/sales/{non_existent_id}/points",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"


# -----------------------------------------------------------------------------
# TEST 5: Invalid Sale ID Value (<= 0)
# Partitions covered:
#   - sale_id value: <= 0 --> BadRequestError, 400
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", [0, -5])
def test_5_get_sale_points_invalid_id_value(client, auth_tokens, role, invalid_id):
    """
    Test 5: Verify error when sale_id is non-positive.
    """
    # Action
    response = client.get(
        f"{BASE_URL}/sales/{invalid_id}/points",
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
def test_6_get_sale_points_invalid_id_type(client, auth_tokens, role, invalid_id):
    """
    Test 6: Verify error when sale_id is not an integer.
    """
    # Action
    response = client.get(
        f"{BASE_URL}/sales/{invalid_id}/points",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# TEST 7: Unauthenticated
# Partitions covered:
#   - User type: Unauthenticated --> UnauthorizedError, 401
# -----------------------------------------------------------------------------
def test_7_get_sale_points_unauthenticated(client):
    """
    Test 7: Verify unauthenticated users cannot access points.
    """
    # Action
    response = client.get(f"{BASE_URL}/sales/1/points")

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"