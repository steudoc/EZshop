Integration steps:

1: card_repository

2: card_repository + card_controller

3: card_repository + customer_repository

4: card_repository + customer_repository + customer_controller

5: card_repository + customer_repository + card_controller + 

customer_controller + card_route + customer_route

unit testing steps: step 1
API testing steps: step 5



********** card_controller_test.py *****************

| Test case name | Object(s) tested | Test level | Technique used |
| :------------ | :-------------- | :--------: | :------------ |
| card_controller_test.test_create_card() | CardController.create_card() | Integration | WB / decision coverage |
| card_controller_test.test_get_card() | CardController.get_card() | Integration | WB / decision coverage |
| card_controller_test.test_modify_card_points() | CardController.modify_points_card() | Integration | WB / decision coverage |


********** customer_controller_test.py *************

| Test case name | Object(s) tested | Test level | Technique used |
| :------------ | :-------------- | :--------: | :------------ |
| customer_controller_test.test_create_customer() | CustomerController.create_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_get_customer_success() | CustomerController.get_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_get_customer_not_found() | CustomerController.get_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_list_customers_empty() | CustomerController.list_customers() | Integration | WB / decision coverage |
| customer_controller_test.test_list_customers_success() | CustomerController.list_customers() | Integration | WB / decision coverage |
| customer_controller_test.test_attach_card_to_customer_not_found() | CustomerController.attach_card_to_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_attach_card_to_customer_conflict() | CustomerController.attach_card_to_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_attach_card_to_customer_card_switch() | CustomerController.attach_card_to_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_update_customer_without_card() | CustomerController.update_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_update_customer_not_found() | CustomerController.update_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_update_customer_with_card() | CustomerController.update_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_update_customer_empty_card() | CustomerController.update_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_update_customer_conflict() |  CustomerController.update_customer()| Integration | WB / decision coverage |
| customer_controller_test.test_update_customer_invalid_card() | CustomerController.update_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_delete_customer_without_card() | CustomerController.delete_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_delete_customer_not_fount() | CustomerController.delete_customer() | Integration | WB / decision coverage |
| customer_controller_test.test_delete_customer_without_card() | CustomerController.delete_customer() | Integration | WB / decision coverage |


********** customer_repository_test.py *************

| Test case name | Object(s) tested | Test level | Technique used |
| :------------ | :-------------- | :--------: | :------------ |
| customer_repository_test.test_create_customer() | CustomerRepository.create_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_get_customer_success() | CustomerRepository.get_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_get_customer_not_found() | CustomerRepository.get_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_list_customers_empty() | CustomerRepository.list_customers() | Integration | WB / decision coverage |
| customer_repository_test.test_list_customers_success() | CustomerRepository.list_customers() | Integration | WB / decision coverage |
| customer_repository_test.test_attach_card_to_customer_not_found() | CustomerRepository.attach_card_to_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_attach_card_to_customer_conflict() | CustomerRepository.attach_card_to_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_attach_card_to_customer_card_switch() | CustomerRepository.attach_card_to_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_update_customer_without_card() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_update_customer_not_found() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_update_customer_with_card() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_update_customer_empty_card() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_update_customer_conflict() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_update_customer_invalid_card() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_delete_customer_without_card() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_delete_customer_not_found() | CustomerRepository.update_customer() | Integration | WB / decision coverage |
| customer_repository_test.test_delete_customer_with_card() | CustomerRepository.update_customer() | Integration | WB / decision coverage |


********** mapper_service_customer_test.py *********

| Test case name | Object(s) tested | Test level | Technique used |
| :------------ | :-------------- | :--------: | :------------ |
| mapper_service_customer_test.test_card_dao_to_response_dto() | carddao_to_response_dto() | Integration | WB / decision coverage |
| mapper_service_customer_test.test_customer_dao_to_response_dto_without_card() | customerdao_to_responsedto() | Integration | WB / decision coverage |
| mapper_service_customer_test.test_customer_dao_to_response_dto_with_card() | customerdao_to_responsedto() | Integration | WB / decision coverage |
| mapper_service_customer_test.test_customerdao_and_card_to_dto_without_card() | customerdao_and_card_to_dto() | Integration | WB / decision coverage |
| mapper_service_customer_test.test_customerdao_and_card_to_dto_with_card() | customerdao_and_card_to_dto() | Integration | WB / decision coverage |


********** customer_test.py ************************

| Test case name | Object(s) tested | Test level | Technique used |
| :------------ | :-------------- | :--------: | :------------ |
| customer_test.test_create_card_success_as_admin() | REST API /customers/cards POST | API | BB / Equivalence partitioning |
| customer_test.test_create_card_success_as_cashier() | REST API /customers/cards POST | API | BB / Equivalence partitioning |
| customer_test.test_create_card_success_as_manager() | REST API /customers/cards POST | API | BB / Equivalence partitioning |
| customer_test.test_create_card_unauthenticated() | REST API /customers/cards POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_success_as_admin() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_success_as_cashier() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_success_as_manager() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_multiple_customers() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_missing_fields() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_with_card() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_with_invalid_card() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_with_wrong_card() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_card_conflict() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_create_customer_unauthenticated() | REST API /customers POST | API | BB / Equivalence partitioning |
| customer_test.test_list_customers_success_as_admin() | REST API /customers GET | API | BB / Equivalence partitioning |
| customer_test.test_list_customers_success_as_cashier() | REST API /customers GET | API | BB / Equivalence partitioning |
| customer_test.test_list_customers_success_as_manager() | REST API /customers GET | API | BB / Equivalence partitioning |
| customer_test.test_list_customers_empty() | REST API /customers GET | API | BB / Equivalence partitioning |
| customer_test.test_list_customers_not_empty() | REST API /customers GET | API | BB / Equivalence partitioning |
| customer_test.test_list_customers_unauthenticated() | REST API /customers GET | API | BB / Equivalence partitioning |
| customer_test.test_get_customer_success_as_admin() | REST API /customers/{customer_id} GET | API | BB / Equivalence partitioning |
| customer_test.test_get_customer_success_as_admin() | REST API /customers/{customer_id} GET | API | BB / Equivalence partitioning |
| customer_test.test_get_customer_success_as_admin() | REST API /customers/{customer_id} GET | API | BB / Equivalence partitioning |
| customer_test.test_get_customer_invalid_id() | REST API /customers/{customer_id} GET | API | BB / Equivalence partitioning |
| customer_test.test_get_customer_not_found() | REST API /customers/{customer_id} GET | API | BB / Equivalence partitioning |
| customer_test.test_get_customer_unauthenticated() | REST API /customers/{customer_id} GET | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_success_as_admin() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_success_as_cashier() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_success_as_manager() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_invalid_customer() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_not_found() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_with_card_success() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_invalid_card() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_card_not_found() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_empty_card() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_empty_card_1() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_change_card() |  REST API /customers/{customer_id} PUT| API | BB / Equivalence partitioning |
| customer_test.test_update_customer_conflict() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_with_card_negative_points() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_update_customer_unauthenticated() | REST API /customers/{customer_id} PUT | API | BB / Equivalence partitioning |
| customer_test.test_delete_customer_success_as_admin() | REST API /customers/{customer_id} DELETE | API | BB / Equivalence partitioning |
| customer_test.test_delete_customer_success_as_cashier() | REST API /customers/{customer_id} DELETE | API | BB / Equivalence partitioning |
| customer_test.test_delete_customer_success_as_manager() | REST API /customers/{customer_id} DELETE | API | BB / Equivalence partitioning |
| customer_test.test_delete_customer_not_found() | REST API /customers/{customer_id} DELETE | API | BB / Equivalence partitioning |
| customer_test.test_delete_customer_unauthenticated() | REST API /customers/{customer_id} DELETE | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_success_as_admin() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_success_as_cashier() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_success_as_manager() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_invalid_customer() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_invalid_card() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_card_not_found() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_customer_not_found() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_card_already_attached() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_twice() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_customer_already_has_card() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_attach_card_to_customer_customer_unauthenticated() | REST API /customers/cards PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_success_as_admin() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_success_as_cashier() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_success_as_manager() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_invalid_id() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_card_not_found() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_success_as_manager() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |
| customer_test.test_modify_card_points_success_unauthenticated() | REST API /customers/cards/{card_id} PATCH | API | BB / Equivalence partitioning |


********** card_repository_test.py *****************

| Test case name | Object(s) tested | Test level | Technique used |
| :------------ | :-------------- | :--------: | :------------ |
| card_repository_test.test_create_card() | CardRepository.create_card() | Unit | WB / decision coverage |
| card_repository_test.test_get_card()_success | CardRepository.get_card() | Unit | WB / decision coverage |
| card_repository_test.test_get_card_not_found() | CardRepository.get_card() | Unit | WB / decision coverage |
| card_repository_test.test_update_card()_success | CardRepository.update_card() | Unit | WB / decision coverage |
| card_repository_test.test_update_card_not_found() | CardRepository.update_card() | Unit | WB / decision coverage |
| card_repository_test.test_update_card_without_sum()_success | CardRepository.update_card_without_sum() | Unit | WB / decision coverage |
| card_repository_test.test_update_card_without_sum_not_found() | CardRepository.update_card_without_sum() | Unit | WB / decision coverage |
| card_repository_test.test_delete_card_success() | CardRepository.delete_card() | Unit | WB / decision coverage |
| card_repository_test.test_delete_card_not_found() | CardRepository.delete_card() | Unit | WB / decision coverage |
| card_repository_test.test_update_and_attach_to_customer_success() | CardRepository.update_and_attach_card_to_customer() | Unit | WB / decision coverage |
| card_repository_test.test_update_and_attach_to_customer_not_found() | CardRepository.update_and_attach_card_to_customer() | Unit | WB / decision coverage |
| card_repository_test.test_is_attached_success() | CardRepository.is_attached() | Unit | WB / decision coverage |
| card_repository_test.test_is_attached_not_found() | CardRepository.is_attached() | Unit | WB / decision coverage |
| card_repository_test.test_get_card_by_customer_success() | CardRepository.get_card_by_customer() | Unit | WB / decision coverage |
| card_repository_test.test_get_card_by_customer_not_found() | CardRepository.get_card_by_customer() | Unit | WB / decision coverage |

# TODO: remove?
| card_repository_test.test_get_card_by_id() |  | Unit | WB / decision coverage |
