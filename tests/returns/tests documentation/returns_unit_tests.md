# Return repository unit tests

## Start return
Prototype of unit: start_return(self, sale_id: int) -> ReturnDAO

Assumptions: sale_id is valid and the user is authenticated 

Criteria: 
+ Valid sale state: yes/no
+ Return found: yes/no

| Valid sale state | Return found | Tests response|
| :--------------: | :----------: | :-----------: |
| no               | any          | 420           |
| yes              | no           | 404           |
| yes              | yes          | 201           |

## Get return by id
Prototype of unit: get_return_by_id(self, return_id: int) -> Optional[ReturnDAO]

Assumptions: return_id is valid and the user is authenticated 

Criteria:
+ Return found: yes/no

| Return found | Tests response|
| :----------: | :-----------: |
| no           | 404           |
| yes          | 200           |

## Get returns by sale
Prototype of unit: get_returns_by_sale(self, sale_id: int) -> list[ReturnDAO]

Assumptions: sale_id is valid and the user is authenticated 

Criteria:
+ Number of returns: 0 or >0

## Get all returns
Prototype of unit: get_all_returns(self) -> list[ReturnDAO]

Assumption: the user is authenticated 

Criteria: 
+ Number of transactions: 0 or >0

## Update return - Funzione probabilmente mai usata
Prototype of unit: update_return(
                                    self,
                                    return_id: int,
                                    updated_sale_id: int, 
                                    updated_status: int, 
                                    updated_created_at: datetime, 
                                    updated_closed_at: datetime
                                ) -> Optional[ReturnDAO]

## Delete return
Prototype of unit: delete_return(self, return_id: int) -> bool

Assumptions: return_id is valid and the user is authenticated 

Criteria:
+ Return found: yes/no
+ Reimbursed transaction: yes/no

| Return found | Reimbursed   | Tests response|
| :----------: | :----------: | :-----------: |
| no           | no           | 404           |
| yes          | yes          | 420           |
| yes          | no           | 204           |
## Add item 
Prototype of unit: add_item(self, return_id: int, item: ReturnItemDTO) -> Optional[ReturnDAO]

Assumptions: input values are validated, the user is authenticated

Criteria: 
+ Valid sale state: yes/no
+ Return found: yes/no

| Valid sale state | Return found | Tests response|
| :--------------: | :----------: | :-----------: |
| no               | no           | 420           |
| no               | yes          | 420           |
| yes              | no           | 404           |
| yes              | yes          | 201           |

## Remove item
Prototype of unit: remove_item(self, return_id: int, product_barcode: str) -> Optional[ReturnDAO]

Assumptions: return_id is valid and the user is authenticated 

Criteria: 
+ Valid sale state: yes/no
+ Return found: yes/no

| Valid sale state | Return found | Tests response|
| :--------------: | :----------: | :-----------: |
| no               | no           | 420           |
| no               | yes          | 420           |
| yes              | no           | 404           |
| yes              | yes          | 201           |

## Close return
Prototype of unit: close_return(self, return_id: int) -> Optional[ReturnDAO]

Assumptions: return_id is valid and the user is authenticated 

Criteria: 
+ Valid sale state: yes/no
+ Return found: yes/no

| Valid sale state | Return found | Tests response|
| :--------------: | :----------: | :-----------: |
| no               | no           | 420           |
| no               | yes          | 420           |
| yes              | no           | 404           |
| yes              | yes          | 201           |

## Reimburse return
Prototype of unit: reimburse_return(self, return_id: int) -> Optional[ReturnDAO]

Assumptions: return_id is valid and the user is authenticated 

Criteria: 
+ Valid sale state: yes/no
+ Return found: yes/no

| Valid sale state | Return found | Tests response|
| :--------------: | :----------: | :-----------: |
| no               | no           | 420           |
| no               | yes          | 420           |
| yes              | no           | 404           |
| yes              | yes          | 201           |




<br><br><br><br>
# Return controller unit tests
Controllers are based on repository, so I will use mock and I will readapt repository tests.

<!-- 

## Start return
Prototype of unit: start_return(self, sale_id: int) -> ReturnDTO:

## Get return by id
Prototype of unit: get_return_by_id(self, return_id: int) -> Optional[ReturnDTO]

## Get returns by sale
Prototype of unit: get_returns_by_sale(self, sale_id: int) -> List[ReturnDTO]

## Get all returns
Prototype of unit: get_all_returns(self) -> List[ReturnDTO]

## Delete return
Prototype of unit: delete_return(self, return_id: int) -> bool

## Add item 
Prototype of unit: add_item(self, return_id: int, item: ReturnItemDTO) -> ReturnDTO

## Remove item
Prototype of unit: remove_item(self, return_id: int, product_barcode: str) -> ReturnDTO:

## Close return
Prototype of unit: close_return(self, return_id: int) -> Optional[bool]

## Reimburse return
Prototype of unit: reimburse_return(self, return_id: int) -> ReturnReimburseDTO

-->


Da chiedere: come faccio a testare le routes?


<br><br><br><br>
# Return route unit tests


## Create return transaction
Prototype of unit: start_return(self, sale_id: int) -> ReturnDAO

## Get return by id
Prototype of unit: get_return_by_id(self, return_id: int) -> ReturnDAO | None

## Get returns by sale
Prototype of unit:

## Get all returns
Prototype of unit:

## Update return
Prototype of unit:

## Delete return
Prototype of unit:
## Add item 
Prototype of unit:

## Remove item
Prototype of unit:

## Close return
Prototype of unit:

## Reimburse return
Prototype of unit:




# TODO : testare anche i vari tipi di output