

# **Integration Approach**

The integration approach adopted for the product management module is **bottom-up**. This strategy allowed for the verification of components starting from the lowest levels (data access) up to the exposure of the APIs:

- **Step 1: Unit Testing (`ProductRepository`)**: In this phase, individual repository methods were tested in isolation. **Mocking** techniques were used to simulate SQLAlchemy database sessions, allowing for the verification of barcode validation logic (GTIN checksum algorithm), proper exception handling (e.g., `NotFoundError`, `ConflictError`), and data integrity at an atomic level.
    
- **Step 2: Integration Testing (`ProductController`)**: Integration tests focused on the interaction between the controller and a real database (SQLite). In each test, the database was reset and reinitialized to ensure execution independence. Complex business logic was verified, such as checking for position conflicts (two products in the same location) and the secure incrementing/decrementing of operation counters (`involvedOperations`).
    
- **Step 3: API/System Testing (`FastAPI/TestClient`)**: The final step involved testing the entire system through simulated HTTP requests. In addition to end-to-end functional flows, security constraints related to user roles (Admin, ShopManager, Cashier) were tested via JWT tokens. Product "locked" states were also verified, preventing, for example, barcode modification or deletion if the product is associated with an open sale.
    

---

### **Test Cases**

|**Test Case Name**|**Tested Object**|**Level**|**Technique**|
|---|---|---|---|
|`test_update_product_invalid_data`|`ProductRepository`|Unit|BB: Boundary Value Analysis|
|`test_update_product_simple_fields`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_update_product_not_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_update_barcode_success`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_update_barcode_conflict`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_update_barcode_invalid_state`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_delete_product_success`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_delete_product_not_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_delete_product_invalid_state`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_get_product_by_barcode_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_get_product_by_barcode_not_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_get_product_by_barcode_invalid_format`|`ProductRepository`|Unit|BB: Boundary Value Analysis|
|`test_get_product_by_id_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_get_product_by_id_not_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_include_product_in_op_increment_success`|`ProductRepository`|Unit|WB: Statement Coverage|
|`test_include_product_in_op_decrement_success`|`ProductRepository`|Unit|WB: Statement Coverage|
|`test_include_product_in_op_decrement_below_zero`|`ProductRepository`|Unit|BB: Boundary Value Analysis|
|`test_include_product_in_op_not_found`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_is_position_free_yes`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_is_position_free_no`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_is_position_free_invalid_format`|`ProductRepository`|Unit|BB: Boundary Value Analysis|
|`test_list_products_populated`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_list_products_empty`|`ProductRepository`|Unit|BB: Equivalence Partitioning|
|`test_create_product_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_create_product_defaults_valid`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_create_product_invalid_barcode`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_create_product_invalid_position_format`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_create_product_conflict_position`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_create_product_conflict_barcode`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_delete_product_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_delete_product_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_delete_product_invalid_state`|`ProductController`|Integration|BB: Equivalence Partitioning|
|**`test_include_product_in_op_success`**|**`ProductController`**|**Integration**|**WB: Statement Coverage**|
|**`test_include_product_in_op_multiple_times`**|**`ProductController`**|**Integration**|**BB: Equivalence Partitioning**|
|**`test_include_product_in_op_not_found`**|**`ProductController`**|**Integration**|**BB: Equivalence Partitioning**|
|`test_exclude_product_from_op_success`|`ProductController`|Integration|WB: Statement Coverage|
|`test_exclude_product_from_op_success_to_zero`|`ProductController`|Integration|WB: Statement Coverage|
|`test_exclude_product_from_op_bad_request`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_exclude_product_from_op_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_get_product_by_barcode_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_get_product_by_barcode_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_get_product_by_barcode_invalid_format`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_get_product_by_id_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_get_product_by_id_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_search_by_description_partial_match`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_search_by_description_case_insensitive`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_search_by_description_no_match`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_search_by_description_empty_db`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_list_products_empty`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_list_products_populated`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_increment_quantity_add_success`|`ProductController`|Integration|WB: Statement Coverage|
|`test_increment_quantity_subtract_success`|`ProductController`|Integration|WB: Statement Coverage|
|`test_increment_quantity_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_increment_quantity_bad_request_negative_result`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_move_product_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_move_product_reset_position`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_move_product_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_move_product_conflict`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_move_product_invalid_format`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_update_product_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_update_product_move_position_success`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_update_product_reset_position`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_update_product_not_found`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_update_product_conflict_position`|`ProductController`|Integration|BB: Equivalence Partitioning|
|`test_update_product_bad_request_quantity`|`ProductController`|Integration|BB: Boundary Value Analysis|
|`test_assign_position_lifecycle`|API Endpoints|API|BB: Scenario Testing|
|`test_assign_position_conflict`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_assign_position_forbidden_cashier`|API Endpoints|API|BB: Access Control|
|`test_assign_position_not_found`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_assign_position_invalid_format`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_assign_position_invalid_id`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_assign_position_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_create_product_success_valid_gtin_and_position`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_create_product_insufficient_permissions`|API Endpoints|API|BB: Access Control|
|`test_create_product_invalid_input`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_create_product_conflict_duplicate_barcode`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_delete_product_success`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_delete_product_forbidden_cashier`|API Endpoints|API|BB: Access Control|
|`test_delete_product_not_found`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_delete_product_invalid_id`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_delete_product_invalid_state_transaction_exists`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_delete_product_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_get_by_barcode_success`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_get_by_barcode_forbidden_cashier`|API Endpoints|API|BB: Access Control|
|`test_get_by_barcode_not_found`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_get_by_barcode_bad_request`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_get_by_barcode_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_get_by_barcode_missing_barcode_param`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_get_product_by_id_success`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_get_product_by_id_not_found`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_get_product_by_id_bad_request_invalid_id`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_get_product_by_id_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_increment_quantity_success`|API Endpoints|API|WB: Statement Coverage|
|`test_decrement_quantity_success`|API Endpoints|API|WB: Statement Coverage|
|`test_decrement_quantity_insufficient_stock`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_quantity_forbidden_cashier`|API Endpoints|API|BB: Access Control|
|`test_quantity_not_found`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_quantity_invalid_id`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_quantity_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_list_products_empty`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_list_products_success_all_roles`|API Endpoints|API|BB: Access Control|
|`test_list_products_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_search_products_success_partial_match`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_search_products_success_single_match`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_search_products_no_match`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_search_products_forbidden_cashier`|API Endpoints|API|BB: Access Control|
|`test_search_products_unauthenticated`|API Endpoints|API|BB: Access Control|
|`test_search_products_missing_query_param`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_update_product_success`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_update_product_forbidden_cashier`|API Endpoints|API|BB: Access Control|
|`test_update_product_not_found`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_update_product_validation_error`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_update_product_invalid_id`|API Endpoints|API|BB: Boundary Value Analysis|
|`test_update_product_conflict_barcode`|API Endpoints|API|BB: Equivalence Partitioning|
|`test_update_barcode_fails_if_transaction_exists`|API Endpoints|API|BB: Scenario Testing|
|`test_update_other_fields_allowed_with_transaction`|API Endpoints|API|BB: Scenario Testing|

---

#### **Coverage of Functional Requirements (FR)**

|**Functional Requirement / Scenario**|**Tests**|
|---|---|
|**FR3.1** – Define/Modify product type|`test_create_product_success`<br><br>  <br><br>`test_update_product_success`<br><br>  <br><br>`test_create_product_success_valid_gtin_and_position`|
|**FR3.2** – Delete a product type|`test_delete_product_success`<br><br>  <br><br>`test_delete_product_invalid_state`|
|**FR3.3** – List all product types|`test_list_products_populated`<br><br>  <br><br>`test_list_products_empty`<br><br>  <br><br>`test_list_products_success_all_roles`|
|**FR3.4** – Search product type|`test_get_product_by_barcode_found`<br><br>  <br><br>`test_get_by_barcode_success`<br><br>  <br><br>`test_search_products_success_partial_match`<br><br>  <br><br>`test_search_by_description_partial_match`|
|**FR4.1** – Modify quantity available|`test_increment_product_quantity`<br><br>  <br><br>`test_increment_quantity_success`<br><br>  <br><br>`test_decrement_quantity_success`<br><br>  <br><br>**`test_include_product_in_op_success`**<br><br>  <br><br>**`test_include_product_in_op_multiple_times`**|
|**FR4.2** – Modify position|`test_move_product_success`<br><br>  <br><br>`test_assign_position_lifecycle`<br><br>  <br><br>`test_update_product_move_position_success`|
|**NFR4** – Barcode Algorithm (GTIN)|`test_get_product_by_barcode_invalid_format`<br><br>  <br><br>`test_create_product_invalid_input`<br><br>  <br><br>`test_update_product_validation_error`|
|**Scenario 1-1** – Create product type $X$|`test_create_product_success_valid_gtin_and_position`|
|**Scenario 1-2** – Modify product type location|`test_update_product_move_position_success`<br><br>  <br><br>`test_move_product_success`<br><br>  <br><br>`test_assign_position_lifecycle`|
|**Scenario 1-3** – Modify product type price|`test_update_product_success`<br><br>  <br><br>`test_update_product_simple_fields`|