import pytest
from utils_route import BASE_URL, auth_header, create_open_sale

# -----------------------------------------------------------------------------
# TESTS FOR GET /sales/{sale_id}
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: All Authorized Roles
# Covers:
# - User type: Administrator, ShopManager, Cashier
# - sale_id type: Int
# - sale_id value: > 0
# - Sale presence: Yes
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_get_sale_success_authorized_roles(client, auth_tokens, role):
    """
    Test 1: Check that all authorized roles can retrieve an existing sale.
    """
    # Setup: Create a sale to ensure presence = Yes
    sale_id = create_open_sale(client, auth_tokens[role])
    
    # Action: Get the sale
    response = client.get(
        f"{BASE_URL}/sales/{sale_id}", 
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sale_id
    # Validating structure based on Swagger definition
    assert "status" in data
    assert "lines" in data

# -----------------------------------------------------------------------------
# TEST 2: Sale Not Found - All Authorized Roles
# Covers:
# - User type: Administrator, ShopManager, Cashier
# - sale_id type: Int
# - sale_id value: > 0
# - Sale presence: No (NotFoundError, 404)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_get_sale_not_found(client, auth_tokens, role):
    """
    Test 2: Check behavior when sale does not exist for all authorized roles.
    """
    # Setup
    non_existent_id = 9999999
    
    # Action
    response = client.get(
        f"{BASE_URL}/sales/{non_existent_id}", 
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 404
    assert response.json()["name"] == "NotFoundError"

# -----------------------------------------------------------------------------
# TEST 3: Invalid ID Value (<= 0) - All Authorized Roles
# Covers:
# - User type: Administrator, ShopManager, Cashier
# - sale_id type: Int
# - sale_id value: <= 0 (BadRequestError, 400)
# - Sale presence: Irrelevant
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id", [0, -1, -50])
def test_3_get_sale_invalid_value_int(client, auth_tokens, role, invalid_id):
    """
    Test 3: Check validation for invalid integer IDs (<=0).
    """
    # Action
    response = client.get(
        f"{BASE_URL}/sales/{invalid_id}", 
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 400
    assert response.json()["name"] == "BadRequestError"

# -----------------------------------------------------------------------------
# TEST 4: Invalid ID Type (String/Float) - All Authorized Roles
# Covers:
# - User type: Administrator, ShopManager, Cashier
# - sale_id type: String, Float
# - Sale presence: Irrelevant
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
@pytest.mark.parametrize("invalid_id_value", ["invalid_string", 1.5])
def test_4_get_sale_invalid_type(client, auth_tokens, role, invalid_id_value):
    """
    Test 4: Check validation for invalid ID types (String, Float).
    """
    # Action
    response = client.get(
        f"{BASE_URL}/sales/{invalid_id_value}", 
        headers=auth_header(auth_tokens, role)
    )
    
    # Assertion
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# TEST 5: Unauthenticated User
# Covers:
# - User type: Unauthenticated (UnauthorizedError, 401)
# -----------------------------------------------------------------------------
def test_5_get_sale_unauthenticated(client, auth_tokens):
    """
    Test 5: Check access for unauthenticated user.
    """
    # Action: No headers provided
    response = client.get(f"{BASE_URL}/sales/1")
    
    # Assertion
    assert response.status_code == 401, f"{response.text}"
    assert response.json()["name"] == "UnauthorizedError"