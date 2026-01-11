BASE_URL = "http://127.0.0.1:8000/api/v1"

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def auth_header(tokens, role: str):
    return {"Authorization": tokens[role]}

def create_product(client, auth_tokens, barcode="123456789012", quantity=100, price_per_unit=10.0):
    """Helper to create a product for sales setup."""
    product_data = {
        "description": "Test Product",
        "barcode": barcode,
        "price_per_unit": price_per_unit,
        "note": "Test Note",
        "quantity": quantity
    }
    response = client.post(f"{BASE_URL}/products", json=product_data, headers=auth_header(auth_tokens, "admin"))
    assert response.status_code == 201, f"Create product failed. Expected 201, got {response.status_code}. Body: {response.text}"
    return barcode

def get_product(client, auth_tokens, barcode):
    """Helper to check product quantity."""
    response = client.get(f"{BASE_URL}/products/barcode/{barcode}", headers=auth_header(auth_tokens, "admin"))
    assert response.status_code == 200, f"Get product qty failed. Expected 200, got {response.status_code}. Body: {response.text}"
    return response.json()

def add_item_to_sale(client, token, sale_id, barcode, amount=1):
    """Helper to add an item to a sale."""
    response = client.post(
        f"{BASE_URL}/sales/{sale_id}/items?barcode={barcode}&amount={amount}",
        headers={"Authorization": token}
    )
    assert response.status_code == 201, f"Add item failed. Expected 201, got {response.status_code}. Body: {response.text}"

def create_open_sale(client, token):
    """Helper to create an OPEN sale."""
    response = client.post(f"{BASE_URL}/sales", headers={"Authorization": token})
    assert response.status_code == 201, f"Create sale failed. Expected 201, got {response.status_code}. Body: {response.text}"
    return response.json()["id"]

def close_sale(client, token, sale_id):
    """Helper to close a sale (Change status to PENDING)."""
    response = client.patch(f"{BASE_URL}/sales/{sale_id}/close", headers={"Authorization": token})
    assert response.status_code == 200, f"Close sale failed. Expected 200, got {response.status_code}. Body: {response.text}"

def pay_sale(client, token, sale_id, amount):
    """Helper to pay a sale (Change status to PAID)."""
    response = client.patch(
        f"{BASE_URL}/sales/{sale_id}/pay?cash_amount={amount}", 
        headers={"Authorization": token}
    )
    assert response.status_code == 200, f"Pay sale failed. Expected 200, got {response.status_code}. Body: {response.text}"

def get_system_balance(client, auth_tokens):
    """Helper to get current system balance (Requires Admin)."""
    response = client.get(
        f"{BASE_URL}/balance", 
        headers=auth_header(auth_tokens, "admin")
    )
    assert response.status_code == 200, f"Get system balance failed. Expected 200, got {response.status_code}. Body: {response.text}"
    return response.json()["balance"]

def create_pending_sale_with_items(client, auth_tokens, role, items=None):
    """Helper to create a PENDING sale"""

    if items is None:
        items = []

    sale_id = create_open_sale(client, auth_tokens[role])

    if not items:
        create_product(client, auth_tokens, "123456789012", 100)
        items.append(("123456789012",10))

    total_cost = 0.0
    for barcode, amount in items:
        add_item_to_sale(client, auth_tokens[role], sale_id, barcode, amount)
        price = get_product(client, auth_tokens, barcode)["price_per_unit"]
        total_cost += price * amount

    close_sale(client, auth_tokens[role], sale_id)
    return sale_id, total_cost

def create_paid_sale_with_items(client, auth_tokens, role, items=None):
    """Helper to create a PAID sale"""
    sale_id, total_cost = create_pending_sale_with_items(client, auth_tokens, role, items)
    pay_sale(client, auth_tokens[role], sale_id, total_cost)
    return sale_id


