# **Integration Approach**

The integration approach adopted for the return management module is **bottom-up**. This strategy allowed for the verification of components starting from the lowest levels (data access) up to the exposure of the APIs:

- **Step 1: Unit Testing (`ReturnRepository`)**: In this phase, individual repository methods were tested in isolation. **Mocking** techniques were used to simulate SQLAlchemy database sessions.
    
- **Step 2: Integration Testing (`ReturnController`)**: Integration tests focused on the interaction between the controller and a real database (SQLite). In each test, the database was reset and reinitialized to ensure execution independence.
    
- **Step 3: API/System Testing (`FastAPI/TestClient`)**: The final step involved testing the entire system through simulated HTTP requests. In addition to end-to-end functional flows, security constraints related to user roles (Admin, ShopManager, Cashier) were tested via JWT tokens. In order to properly enable and validate return-related tests, the APIs for customers, sales, balance, and system management were also invoked, as these components are required for the correct execution of return operations.

---

### **Test Cases**

|**Test Case Name**|**Tested Object**|**Level**|**Technique**|
|---|---|---|---|
|`return_repository_add_item_test`|`ReturnRepository.add_item`|Unit|WB:Multiple Condition Coverage|
|`return_repository_close_return_test`|`ReturnRepository.close_return`|Unit|WB:Multiple Condition Coverage|
|`return_repository_delete_transaction_test`|`ReturnRepository.delete_return`|Unit|WB:Multiple Condition Coverage|
|`return_repository_get_all_returns_test`|`ReturnRepository.get_all_returns`|Unit|WB:Multiple Condition Coverage|
|`return_repository_get_return_by_id_test`|`ReturnRepository.get_return_by_id`|Unit|WB:Multiple Condition Coverage|
|`return_repository_get_return_by_sale_id_test`|`ReturnRepository.get_returns_by_sale`|Unit|WB:Multiple Condition Coverage|
|`return_repository_reimburse_test`|`ReturnRepository.reimburse_return`|Unit|WB:Multiple Condition Coverage|
|`return_repository_remove_item_test`|`ReturnRepository.remove_item`|Unit|WB:Multiple Condition Coverage|
|`return_repository_start_return_test`|`ReturnRepository.start_return`|Unit|WB:Multiple Condition Coverage|
|`return_controller_add_item_test`|`ReturnController.add_item`|Integration|WB:Multiple Condition Coverage|
|`return_controller_close_return_test`|`ReturnControlle.close_return`|Integration|WB:Multiple Condition Coverage|
|`return_controller_delete_transaction_test`|`ReturnController.delete_return`|Integration|WB:Multiple Condition Coverage|
|`return_controller_get_all_return_test`|`ReturnController.get_all_returns`|Integration|WB:Multiple Condition Coverage|
|`return_controller_get_return_by_id_test`|`ReturnController.get_return_by_id`|Integration|WB:Multiple Condition Coverage|
|`return_controller_get_return_by_sale_id_test`|`ReturnController.get_returns_by_sale`|Integration|WB:Multiple Condition Coverage|
|`return_controller_reimburse_test`|`ReturnController.reimburse_return`|Integration|WB:Multiple Condition Coverage|
|`return_controller_remove_item_test`|`ReturnController.remove_item`|Integration|WB:Multiple Condition Coverage|
|`return_controller_start_return_test`|`ReturnController.start_return`|Integration|WB:Multiple Condition Coverage|
|`return_route_add_item_test`|`ReturnRoute.add_item`|API/System|BB:Equivalence classes partitioning|
|`return_route_close_return_test`|`ReturnRoute.close_return`|API/System|BB:Equivalence classes partitioning|
|`return_route_delete_transaction_test`|`ReturnRoute.delete_return`|API/System|BB:Equivalence classes partitioning|
|`return_route_get_all_returns_test`|`ReturnRoute.get_all_returns`|API/System|BB:Equivalence classes partitioning|
|`return_route_get_return_by_id_test`|`ReturnRoute.get_return_by_id`|API/System|BB:Equivalence classes partitioning|
|`return_route_get_returns_by_sale_test`|`ReturnRoute.get_returns_by_sale`|API/System|BB:Equivalence classes partitioning|
|`return_route_reimburse_test`|`ReturnRoute.reimburse_return`|API/System|BB:Equivalence classes partitioning|
|`return_route_remove_item_test`|`ReturnRoute.remove_item`|API/System|BB:Equivalence classes partitioning|
|`return_route_start_return_test`|`ReturnRoute.start_return`|API/System|BB:Equivalence classes partitioning|

---

#### **Coverage of Functional Requirements (FR)**

|**Functional Requirement / Scenario**|**Tests**|
|---|---|
|**FR6.12** – Start a return transaction|`return_repository_start_return_test`<br>`return_controller_start_return_test`<br>`return_route_start_return_test`<br>| 
|**FR6.13** – Return a product listed in a sale transaction|`return_repository_add_item_test`<br>`return_controller_add_item_test`<br>`return_route_add_item_test`<br>| 
|**FR6.14** – Close a return transaction|`return_repository_close_return_test`<br>`return_controller_close_return_test`<br>`return_route_close_return_test`<br>| 
|**FR6.15** – Rollback or commit a closed return transaction|`return_repository_reimburse_test`<br>`return_controller_reimburse_test`<br>`return_route_reimburse_test`<br>| 
|**Scenario 8-1** – Return transaction of product type X completed, credit card|`return_repository_start_return_test`<br>`return_repository_add_item_test`<br>`return_repository_reimburse_test`<br>`return_repository_close_return_test`<br><br>`return_controller_start_return_test`<br>`return_controller_add_item_test`<br>`return_controller_reimburse_test`<br>`return_controller_close_return_test`<br><br>`return_route_start_return_test`<br>`return_route_add_item_test`<br>`return_route_reimburse_test`<br>`return_route_close_return_test`|
|**Scenario 8-2** – Return transaction of product type X completed, cash|`return_repository_start_return_test`<br>`return_repository_add_item_test`<br>`return_repository_reimburse_test`<br>`return_repository_close_return_test`<br><br>`return_controller_start_return_test`<br>`return_controller_add_item_test`<br>`return_controller_reimburse_test`<br>`return_controller_close_return_test`<br><br>`return_route_start_return_test`<br>`return_route_add_item_test`<br>`return_route_reimburse_test`<br>`return_route_close_return_test`|
