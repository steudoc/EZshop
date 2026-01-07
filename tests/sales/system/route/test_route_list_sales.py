import pytest
from utils_route import BASE_URL, auth_header, create_open_sale

# -----------------------------------------------------------------------------
# TESTS FOR GET /sales
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# TEST 1: List Sales (> 0 Sales)
# Partition covered:
#   - User type: Administrator, ShopManager, Cashier
#   - Number of sales present: > 0
# Expected: 200 OK
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_1_list_sales_success_with_data(client, auth_tokens, role):
    """
    Test 1: Verify that authorized users can retrieve a list of sales when sales exist.
    """
    # Setup: Create a Sale to ensure 'Number of sales present > 0'
    created_sale_id = create_open_sale(client, auth_tokens[role])

    # Action: List all sales
    response = client.get(
        f"{BASE_URL}/sales",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 200
    data = response.json()
    
    # Assertion: Verify the response is a list
    assert isinstance(data, list)
    
    # Assertion: Verify the created sale is in the list
    sale_ids = [sale["id"] for sale in data]
    assert created_sale_id in sale_ids


# -----------------------------------------------------------------------------
# TEST 2: List Sales (0 Sales)
# Partition covered:
#   - User type: Administrator, ShopManager, Cashier
#   - Number of sales present: 0
# Expected: 200 OK
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("role", ["admin", "manager", "cashier"])
def test_2_list_sales_success_empty(client, auth_tokens, role):
    """
    Test 2: Verify that authorized users receive an empty list (or valid list) 
    when no NEW sales are present.
    """
    # Action
    response = client.get(
        f"{BASE_URL}/sales",
        headers=auth_header(auth_tokens, role)
    )

    # Assertion
    assert response.status_code == 200
    data = response.json()
    
    # Assertion: It must be a list
    assert isinstance(data, list)
    assert len(data) == 0 


# -----------------------------------------------------------------------------
# TEST 3: List Sales - Unauthorized
# Partition covered:
#   - User type: Unauthenticated
#   - Number of sales present: Irrelevant (0 or >0)
# Expected: 401 UnauthorizedError
# -----------------------------------------------------------------------------
def test_3_list_sales_unauthenticated(client):
    """
    Test 3: Verify that an unauthenticated user cannot list sales.
    """
    # Action: Request without headers
    response = client.get(f"{BASE_URL}/sales")
  
    # Assertion: Verify Error Name and Code
    assert response.status_code == 401
    assert response.json()["name"] == "UnauthorizedError"
