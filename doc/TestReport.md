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

  ![alt text](images/ezshopDependencyGraph.jpeg)

# Integration approach

## Balance tests

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit testing)**: SystemRepository
  - Mocked database session
  - Tests low-level repository methods for getting and setting balance

- **Step 2 (Integration testing)**: SystemRepository + SystemController
  - Real database (reset between tests)
  - Tests controller integration with repository layer
  - Verifies balance operations through controller interface

- **Step 3 (System/API testing)**: Full stack (Controller + Repository + Database + Routes)
  - Uses TestClient to call REST API endpoints
  - Tests complete HTTP flow with authentication
  - Verifies system behavior at API level

## Returns tests

## Sales tests

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit Testing)**: Individual components were tested in isolation using a White Box approach with Simple Decision Coverage:
   - **Mapper Service**: Tested directly without the need for mocks.
   - **Repository**: Tested in isolation by mocking calls to the `ProductRepository` and the underlying database.
   - **Controller**: Tested in isolation by creating stubs (mocks) for functions related to `SaleRepository` and `SystemController`.

- **Step 2 (Integration testing)**: Focused on specific Controller functions (`create_sale`, `list_sales`, `get_sale`). In this step, calls to the Repository remained mocked, but the interaction with the **Mapper Service** (`sale_dao_to_dto`) was real (no mocks), verifying the correct integration between Controller and Mapper. The technique used remained White Box with Simple Decision Coverage.

- **Step 3 (API/System testing)**: The full system was tested at the Route level using a Black Box approach, specifically applying Equivalence Class Partitioning.

## Products test

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit testing)**: In this phase, individual repository methods were tested in isolation. **Mocking** techniques were used to simulate SQLAlchemy database sessions, allowing for the verification of barcode validation logic (GTIN checksum algorithm), proper exception handling (e.g., `NotFoundError`, `ConflictError`), and data integrity at an atomic level.
    
- **Step 2 (Integration testing)**: Integration tests focused on the interaction between the controller and a real database (SQLite). In each test, the database was reset and reinitialized to ensure execution independence. Complex business logic was verified, such as checking for position conflicts (two products in the same location) and the secure incrementing/decrementing of operation counters (`involvedOperations`).
    
- **Step 3 (API/System testing)**: The final step involved testing the entire system through simulated HTTP requests. In addition to end-to-end functional flows, security constraints related to user roles (Admin, ShopManager, Cashier) were tested via JWT tokens. Product "locked" states were also verified, preventing, for example, barcode modification or deletion if the product is associated with an open sale.

## Customers tests

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit Testing)**: CardRepository and CustomerRepository (in isolation)
  - Real database with reset/init between tests
  - Tests repository methods for CRUD operations on customers and cards
  - Each test operates independently with mocked dependencies

- **Step 2 (Integration Testing)**: CardRepository + CustomerRepository + CardController + CustomerController
  - Real database
  - Tests controller orchestration with multiple repositories
  - Verifies customer and card management business logic

- **Step 3 (System/API Testing)**: Full stack (All layers + Routes + HTTP)
  - Uses TestClient for HTTP API testing
  - Tests complete workflows with authentication
  - Verifies customer and card operations through REST endpoints
    
## Orders tests

Integration strategy: **Bottom-up approach**

- **Step 1 (Unit Testing)**: OrderRepository, ProductRepository, SystemRepository (in isolation)
  - Real database with reset/init between tests
  - Tests repository methods for CRUD operations on orders
  - Each test operates independently with mocked dependencies

- **Step 2 (Integration Testing)**: OrderRepository + OrderController + ProductRepository
  - Real database
  - Tests controller orchestration with multiple repositories
  - Verifies order state transitions and business logic

- **Step 3 (System/API Testing)**: Full stack (All layers + Routes + HTTP)
  - Uses TestClient for HTTP API testing
  - Tests complete workflows with authentication
  - Verifies order operations through REST endpoints


# Tests

## Balance tests

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

# Coverage

## Coverage of FR

<Report in the following table the coverage of functional requirements and scenarios(from official requirements) >

| Functional Requirement or scenario | Test(s) |
| :--------------------------------: | :-----: |
|                FRx                 |         |
|                FRy                 |         |
|                Scx                 |         |
|                Scy                 |         |
|                ...                 |         |

## Coverage white box

Report here the screenshot of coverage values obtained with PyTest
