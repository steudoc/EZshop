import pytest
from utils_route import BASE_URL, auth_header

# -----------------------------------------------------------------------------
# TESTS FOR POST /sales
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: Create Sale
# Partition covered:
#   - User type: Administrator
#   - User type: ShopManager
#   - User type: Cashier
#   - Response: 201 Created
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_create_sale_success(client, auth_tokens, role):
    """
    Test 1: Verify that all authorized roles (Administrator, ShopManager, Cashier)
    can successfully start a new sale transaction.
    """
    # Action: Send POST request to create a sale
    response = client.post(
        f"{BASE_URL}/sales",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion: Check Status Code
    assert response.status_code == 201
    
    # Assertion: Check Response Body Structure
    data = response.json()
    
    # The response must contain an ID (positive integer)
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["id"] > 0
    
    # Check default values for a new sale
    # Based on Requirements: Initial status should be OPEN
    assert "status" in data
    assert data["status"] == "OPEN"
        
    # New sales usually have 0.0 discount rate initially
    assert "discount_rate" in data
    assert data["discount_rate"] == 0.0
        
    # New sales should have an empty list of lines (items)
    assert "lines" in data
    assert isinstance(data["lines"], list)
    assert len(data["lines"]) == 0

# -----------------------------------------------------------------------------
# TEST 2: Create Sale - Unauthenticated
# Partition covered:
#   - User type: Unauthenticated
#   - Response: 401 Unauthorized 
# -----------------------------------------------------------------------------
def test_2_create_sale_unauthenticated(client):
    """
    Test 2: Verify that an unauthenticated user cannot start a sale.
    """
    # Action: Send POST request without Authorization header
    response = client.post(f"{BASE_URL}/sales")

    # Assertion
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"