# Test Report

<The goal of this document is to explain how the application was tested, detailing how the test cases were defined and what they cover>

# Contents

- [Test Report](#test-report)
- [Contents](#contents)
- [Dependency graph](#dependency-graph)
- [Integration approach](#integration-approach)
- [Tests](#tests)
- [Coverage](#coverage)
  - [Coverage of FR](#coverage-of-fr)
  - [Coverage white box](#coverage-white-box)

# Dependency graph

     <report the here the dependency graph of EzShop>

# Integration approach

## Package Balance

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit Testing)**: SystemRepository
  - Test: `accounting_repository_get_balance_test.py`, `accounting_repository_set_balance_test.py`
  - Mocked database session
  - Tests low-level repository methods for getting and setting balance

- **Step 2 (Integration Testing)**: SystemRepository + SystemController
  - Tests: `accounting_controller_get_balance_test.py`, `accounting_controller_set_balance_test.py`, `accounting_controller_reset_balance_test.py`
  - Real database (reset between tests)
  - Tests controller integration with repository layer
  - Verifies balance operations through controller interface

- **Step 3 (System/API Testing)**: Full stack (Controller + Repository + Database + Routes)
  - Tests: `accounting_system_get_balance_test.py`, `accounting_system_set_balance_test.py`, `accounting_system_reset_balance_test.py`
  - Uses TestClient to call REST API endpoints
  - Tests complete HTTP flow with authentication
  - Verifies system behavior at API level

## Package Orders

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit Testing)**: OrderRepository, ProductRepository, SystemRepository (in isolation)
  - Tests: `test_unit_create_order.py`, `test_unit_get_order.py`, `test_unit_list_orders.py`, `test_unit_update_issued_order.py`, `test_unit_update_paid_order.py`
  - Real database with reset/init between tests
  - Tests repository methods for CRUD operations on orders
  - Each test operates independently with mocked dependencies

- **Step 2 (Integration Testing)**: OrderRepository + OrderController + ProductRepository
  - Tests: `test_integration_create_issued_order.py`, `test_integration_create_paid_order.py`, `test_integration_pay_order.py`, `test_integration_list_orders.py`, `test_integration_complete_order.py`
  - Real database
  - Tests controller orchestration with multiple repositories
  - Verifies order state transitions and business logic

- **Step 3 (System/API Testing)**: Full stack (All layers + Routes + HTTP)
  - Tests: `test_system_create_issued_order.py`, `test_system_create_paid_order.py`, `test_system_pay_order.py`, `test_system_list_orders.py`, `test_system_complete_order.py`
  - Uses TestClient for HTTP API testing
  - Tests complete workflows with authentication
  - Verifies order operations through REST endpoints

# Tests  

## Package Balance

| Test case name | Object(s) tested | Test level | Technique used |
| :------------: | :--------------: | :--------: | :------------: |
| test_get_balance_success | SystemRepository.get_last_system_info() | Unit | WB: Mocking + Statement coverage |
| test_get_balance_no_system_info | SystemRepository.get_last_system_info() | Unit | WB: Boundary value (None case) |
| test_get_balance_session_error | SystemRepository.get_last_system_info() | Unit | WB: Error handling |
| test_create_system_info_success | SystemRepository.create_system_info() | Unit | WB: Statement coverage + Mocking |
| test_create_system_info_zero_balance | SystemRepository.create_system_info() | Unit | BB: Boundary value (zero) |
| test_create_system_info_negative_balance | SystemRepository.create_system_info() | Unit | BB: Equivalence class (negative) |
| test_create_system_info_failure | SystemRepository.create_system_info() | Unit | WB: Exception handling |
| test_get_balance_success | SystemController.get_balance() | Integration | BB: Equivalence class + Integration testing |
| test_get_balance_zero_value | SystemController.get_balance() | Integration | BB: Boundary value (zero) |
| test_get_balance_not_found | SystemController.get_balance() | Integration | BB: Exception case |
| test_set_balance_success | SystemController.set_balance() | Integration | BB: Valid input + Integration testing |
| test_set_balance_zero | SystemController.set_balance() | Integration | BB: Boundary value (zero) |
| test_set_balance_negative_raises_error | SystemController.set_balance() | Integration | BB: Exception case (negative) |
| test_reset_balance_success | SystemController.reset_balance() | Integration | BB: State transition verification |
| test_get_balance_success | REST API /balance GET | System/API | BB: Full stack + API testing |
| test_get_balance_zero | REST API /balance GET | System/API | BB: Boundary value (zero) |
| test_get_balance_positive_amount | REST API /balance GET | System/API | BB: Equivalence class (positive) |
| test_get_balance_returns_latest | REST API /balance GET | System/API | WB: State consistency |
| test_get_balance_unauthenticated | REST API /balance GET | System/API | BB: Authorization error |
| test_get_balance_without_header | REST API /balance GET | System/API | BB: Missing header error |
| test_get_balance_invalid_token | REST API /balance GET | System/API | BB: Invalid credentials |
| test_get_balance_in_complete_workflow | REST API Balance workflow | System/API | WB: End-to-end scenario |
| test_get_balance_consistency | REST API /balance GET | System/API | WB: Consistency verification |
| test_set_balance_success | REST API /balance/set POST | System/API | BB: Valid input + API testing |
| test_set_balance_zero | REST API /balance/set POST | System/API | BB: Boundary value (zero) |
| test_set_balance_negative_rejected | REST API /balance/set POST | System/API | BB: Invalid input (negative) |
| test_set_balance_then_get | REST API Balance workflow | System/API | WB: Integration verification |
| test_set_balance_overwrites_previous | REST API /balance/set POST | System/API | WB: State overwrite |

## Package Orders

| Test case name | Object(s) tested | Test level | Technique used |
| :------------: | :--------------: | :--------: | :------------: |
| test_create_order_success | OrderRepository.create_order() | Unit | WB: Statement coverage + Mocking |
| test_create_order_paid_with_sufficient_balance | OrderRepository.create_order() + SystemRepository | Unit | BB: Equivalence class (sufficient balance) |
| test_create_order_product_not_found | OrderRepository.create_order() | Unit | BB: Exception case |
| test_create_order_insufficient_balance | OrderRepository.create_order() + SystemRepository | Unit | BB: Boundary value (insufficient balance) |
| test_get_order_existing_order | OrderRepository.get_order() | Unit | WB: Statement coverage |
| test_get_order_non_existent_order | OrderRepository.get_order() | Unit | BB: Boundary value (None case) |
| test_get_order_multiple_orders | OrderRepository.get_order() | Unit | WB: Isolation verification |
| test_list_orders_empty | OrderRepository.list_orders() | Unit | BB: Boundary value (empty list) |
| test_list_orders_single_order | OrderRepository.list_orders() | Unit | BB: Equivalence class (single element) |
| test_list_orders_multiple_orders | OrderRepository.list_orders() | Unit | WB: Statement coverage |
| test_create_issued_order_success | OrderController.create_issued_order() | Integration | BB: Valid input + Integration testing |
| test_create_issued_order_with_zero_quantity | OrderController.create_issued_order() | Integration | BB: Boundary value (zero) |
| test_create_issued_order_with_negative_quantity | OrderController.create_issued_order() | Integration | BB: Equivalence class (negative) |
| test_create_issued_order_with_zero_price | OrderController.create_issued_order() | Integration | BB: Boundary value (zero price) |
| test_pay_order_success | OrderController.pay_order() + SystemController | Integration | BB: State transition + Balance deduction |
| test_pay_order_not_found | OrderController.pay_order() | Integration | BB: Exception case |
| test_pay_order_invalid_id_negative | OrderController.pay_order() | Integration | BB: Boundary value (negative ID) |
| test_pay_order_already_paid | OrderController.pay_order() | Integration | BB: Invalid state |
| test_list_orders | OrderController.list_orders() | Integration | WB: Integration verification |
| test_complete_order_success | OrderController.complete_order() | Integration | BB: State transition |
| test_create_issued_order_system_workflow | Full stack + OrderRepository verification | System | WB: End-to-end scenario |
| test_create_issued_order_with_product_involvement | OrderController + ProductRepository | System | WB: Side effect verification |
| test_create_issued_order_does_not_affect_balance | OrderController + SystemRepository | System | WB: State isolation |
| test_pay_order_system_workflow | Full workflow: Create + Pay + Verify | System | WB: Complete workflow |
| test_pay_order_deducts_correct_amount | OrderController + SystemController | System | BB: Calculation verification |

# Coverage

## Coverage of FR

### Package Balance

| Functional Requirement or scenario | Test(s) |
| :--------------------------------: | :-----: |
| FR8.4 - Compute balance | test_get_balance_success, test_get_balance_zero_value, test_get_balance_zero, test_get_balance_positive_amount, test_get_balance_returns_latest, test_get_balance_consistency |
| FR8.1 - Record debit | test_set_balance_success, test_set_balance_zero, test_set_balance_then_get, test_set_balance_overwrites_previous |
| FR8.2 - Record credit | test_set_balance_success, test_set_balance_then_get |
| FR8.3 - Show credits and debits over a period | test_get_balance_in_complete_workflow |
| Balance error handling | test_set_balance_negative_rejected, test_get_balance_not_found |
| Authentication & Authorization | test_get_balance_unauthenticated, test_get_balance_without_header, test_get_balance_invalid_token |
| Scenario 9-1 - List credits and debits | test_get_balance_in_complete_workflow, test_get_balance_success |

### Package Orders

| Functional Requirement or scenario | Test(s) |
| :--------------------------------: | :-----: |
| FR4.4 - Send and pay an order for a product type | test_create_issued_order_success, test_create_issued_order_system_workflow, test_pay_order_success, test_pay_order_system_workflow |
| FR4.5 - Pay an issued reorder warning | test_pay_order_success, test_pay_order_system_workflow, test_pay_order_deducts_correct_amount |
| FR4.6 - Record order arrival | test_complete_order_success |
| FR4.7 - List all orders (issued, payed, completed) | test_list_orders_empty, test_list_orders_single_order, test_list_orders_multiple_orders, test_list_orders |
| Scenario 3-1 - Order of product type X issued | test_create_issued_order_success, test_create_issued_order_system_workflow, test_create_issued_order_does_not_affect_balance |
| Scenario 3-2 - Order of product type X payed | test_pay_order_success, test_pay_order_system_workflow, test_pay_order_deducts_correct_amount |
| Scenario 3-3 - Record order arrival | test_complete_order_success, test_create_issued_order_with_product_involvement |
| Order validation & error handling | test_create_order_product_not_found, test_create_order_insufficient_balance, test_create_issued_order_with_zero_quantity, test_create_issued_order_with_negative_quantity, test_create_issued_order_with_zero_price, test_pay_order_not_found, test_pay_order_invalid_id_negative, test_pay_order_already_paid |
| Order state transitions | test_create_issued_order_success, test_pay_order_success, test_complete_order_success |
| Balance deduction on payment | test_create_order_paid_with_sufficient_balance, test_pay_order_success, test_pay_order_system_workflow, test_pay_order_deducts_correct_amount |