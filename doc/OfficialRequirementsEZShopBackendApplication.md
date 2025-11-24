# Official Requirements Document - EZ Shop Backend Application





# Contents

- [Context Diagram and interfaces](#context-diagram-and-interfaces)
	+ [Context Diagram](#context-diagram)
	+ [Interfaces](#interfaces) 
	
- [Functional and non functional requirements](#functional-and-non-functional-requirements)
	+ [Functional Requirements](#functional-requirements)
	+ [Non functional requirements](#non-functional-requirements)
- [Use case diagram and use cases](#use-case-diagram-and-use-cases)
	+ [Use case diagram](#use-case-diagram)
	+ [Use cases](#use-cases)
- [Glossary](#glossary)
- [Hardware software architecture](#deployment-diagram)



# Context Diagram and interfaces

## Context Diagram

```plantuml
top to bottom direction
actor EZShopClient 

EZShopClient -> (EZShopBackEndApplication)
 
```

## Interfaces

| Actor | Logical Interface | Physical Interface  |
| ------------- |:-------------|:-----|
| EZShopClient | API as described in EZShopBackEndApplication_swagger.yaml  | internet link |




# Functional and non functional requirements

## Functional Requirements
All FR of EZShop except 7.2 and 7.4 



### Table of rights


Same as for EZShop. All requests to EZShopBackEndApplication come from EZShopClient, 
but carry also, in the authorization token, information about the actor who originally started the request.


## Non Functional Requirements
Same as for EZShop, except NFR1 (no user interface on the server) and NFR5 (since FR7.2 and FR 7.4 are dropped)


# Use case diagram and use cases


## Use case diagram

Same as for EZShop, except UC "Payment by credit card" and "Return by credit card" and related scenarios (7-1 7-2 7-3 8-1 10-1). 
The triggering actor is always 
EZShopClient, but the requests from it carry the original actor triggering the request. 



# Glossary
same as  EZShop glossary 
# Hardware software architecture


```plantuml

node ServerComputer
artifact EZShopBackEndApplication


EZShopBackEndApplication -> ServerComputer
```

