

# Requirements Document - EZShop

Date: 24/10/2025

Version: 1.0.0

| Version number | Change |
| :------------: | :----: |
|                |        |

# Contents

- [Requirements Document - EzShop](#requirements-document)
- [Contents](#contents)
- [Informal description](#informal-description)
- [Business model](#business-model)
- [Stakeholders](#stakeholders)
- [Context Diagram and interfaces](#context-diagram-and-interfaces)
  - [Context Diagram](#context-diagram)
  - [Interfaces](#interfaces)
- [Functional and non functional requirements](#functional-and-non-functional-requirements)
  - [Functional Requirements](#functional-requirements)
  - [Non Functional Requirements](#non-functional-requirements)
- [Table of Rights](#table-of-rights)
- [Use case diagram and use cases](#use-case-diagram-and-use-cases)
  - [Use case diagram](#use-case-diagram)
    - [Use case 1, UC1](#use-case-1-uc1)
      - [Scenario 1.1](#scenario-11)
      - [Scenario 1.2](#scenario-12)
      - [Scenario 1.x](#scenario-1x)
    - [Use case 2, UC2](#use-case-2-uc2)
    - [Use case x, UCx](#use-case-x-ucx)
- [Glossary](#glossary)
- [System Design](#system-design)
- [Hardware Software architecture](#Hardware-software-architecture)

# Informal description

Small shops require a simple application to support the owner or manager. A small shop (ex a food shop) occupies 50-200 square meters, sells 500-2000 different item types, has two or a few more cash registers. 
EZShop is a software application to:
* manage sales
* manage inventory
* manage orders to suppliers
* support accounting

In the following describe the requirements of the EZShop application. 
You are free to define the application as you deem more useful and effective for the stakeholders. 
You are also free to modify the structure of the document when needed.
The document will be evaluated considering the typical defects in requirements (omissions, ambiguities, contradictions, etc), and syntactic errors in the formalism used (UML diagrams). 
Consider that the document should be delivered to another team (unknown to you)
 which will be in charge of designing and implementing the system. The design team should be able to proceed only with the information in the document.

# Business Model

### Customer Segment:
The target customer segment for EZshop is composed of owners of small shops who require a reliable, easy-to-use system to manage everyday store activities. The primary users include the owner and store employees, particularly cashiers, logistic operators and accountants.

### Value Proposition:
EZshop provides a desktop application for managing the main shop activities: sales processing, inventory tracking, suppliers and orders management and basic accounting.
The application can run on multiple computers at the same time, ensuring availability and stability of the shop’s operations even without requiring an internet connection, if the computers are connected to the same local network. EZshop relies on some external system only to manage payments and can work with regular barcode scanners to scan products, so the cost of the solution for shop owners is limited.  

### Revenue Stream:
The shop owner pays an initial fee that covers the software licence(s) and installation, first employees training. After a warranty period, the client will pay for system updates and technical assistance if they need it.


# Stakeholders

| Stakeholder name | Description |
| :--------------: | :--------- |
| Shop owner | Person who holds the role of system administrator |
| Cashier  | Employee responsible for overseeing sales. Their job is to process a customer sale |
| Logistic operator | Employee that manages inventory and handles orders to product suppliers |
| Accountant | Employee who handles the accounting reports created by EZshop |
| Cash station | Hardware and software system that allows customers to pay with cash. It automatically handles transactions and provides cash change. (e.g. [this](https://cashmatic.it/prodotti/selfpay/?gclid=Cj0KCQjwgpzIBhCOARIsABZm7vFn1HBO9fjzIP3ga-uvUXyKMNdOeX9g5ZvEqUyeSzf5ZBjQxBBWzq8aAj3jEALw_wcB)) |
| POS station | Hardware and software system that allows customers to pay with credit cards. It automatically handles transactions with credit card circuits. (e.g. [this](https://www.mypos.com/it-it)) |
| Barcode scanner | Portable scanner (e.g. [this](https://www.amazon.it/Yanzeo-USB-Barcode-Scanner-computer/dp/B07KD4C7WL?pd_rd_w=yKpzM&content-id=amzn1.sym.58ed5d1b-41a3-4c6c-a38c-3416ea9905f1&pf_rd_p=58ed5d1b-41a3-4c6c-a38c-3416ea9905f1&pf_rd_r=TFX7D02PYAGKE88FQ9XH&pd_rd_wg=mBPpY&pd_rd_r=a4f43118-426a-4c39-863c-88847ba043fa&pd_rd_i=B07KD4C7WL&th=1)) which can be used to scan barcodes found in product labels |
| Receipt printer | Dedicated printer system for producing the non-fiscal itemized receipt. (e.g. [this](https://www.amazon.it/NETUM-Stampante-termica-per-ricevute/dp/B0854CCF75?ref_=Oct_d_Oct_d_ss_d_6572840031_1&pd_rd_w=SIutK&content-id=amzn1.sym.3a84fb8b-d4d6-4483-8fd7-0000cb59ea5a&pf_rd_p=3a84fb8b-d4d6-4483-8fd7-0000cb59ea5a&pf_rd_r=X5XJMQ88AS3PNWAM8167&pd_rd_wg=YZ1PH&pd_rd_r=a73378a2-7d7f-458e-ba9d-d6eff854a21d&pd_rd_i=B0854CCF75)) |

# Context Diagram and interfaces

## Context Diagram

\<Define here Context diagram using UML use case diagram>

\<actors are a subset of stakeholders>

## Interfaces


|   Actor   |  Physical Interface | Logical Interface |
| :-------: | :--------------- | :---------------- |
| Shop owner | Monitor, mouse e keyboard / monitor touch| GUI (Graphic User Interface) |
| Cashier  | Monitor, mouse e keyboard / monitor touch | GUI |
| Logistic operator| Monitor, mouse e keyboard / monitor touch | GUI |
| Accountant  | Monitor, mouse e keyboard / monitor touch | GUI |
| Cash station  | Ethernet cable / Bluetooth / USB cable / WiFi | Cash station driver |
| POS station  | Ethernet cable / Bluetooth / USB cable / WiFi | myPOS API: (integration tools and APIs are available [here](https://developers.mypos.com/en)) |
| Barcode scanner |  Bluetooth / USB cable | Operating System API for scanners |
| Receipt printer | Bluetooth / USB cable | Operating System API for printers |


# Functional and non functional requirements

## Functional Requirements

\<In the form DO SOMETHING, or VERB NOUN, describe high level capabilities of the system>

\<they match to high level use cases>

|  ID   | Description |
| :---: | :---------: |
|  FR1  |             |
|  FR2  |             |
| FRx.. |             |

## Non Functional Requirements

\<Describe constraints on functional requirements>

|   ID    | Type (efficiency, reliability, ..) | Description | Refers to |
| :-----: | :--------------------------------: | :--------- | :------- |
|  NFR1 | Usability | After the initial training, even not tech-savvy should be able to use the system | All FR |
| NFR2 | Efficiency | Product information should be gathered in less than 1 second upon code scan | FR1.2, FR2 |
| NFR3 | Efficiency | Monthly sales report should take less than 1 minute to compute | FR4 |
| NFR4 | Efficiency | Stock quantity for products should be updated in less than 10 minutes after transaction | FR2, FR3 |
| NFR5 | Efficiency | Manual discounts should be applied in less than 1 second upon confirmation | FR1.5 |
| NFR6 | Efficiency | All account-related operations should take the system less than then 30s to complete | FR5 |
| NFR7 | Efficiency | All orders for a specific product / specific supplier should be retrieved in less than 10 seconds | FR3 |
| NFR8 | Reliability | Less than a week of downtime per year | All FR |
| NFR9 | Portability | Desktop computer running windows from version 10 | All FR |
| NFR10 | Portability | Software application must be responsive (the size of GUI must change with different size screen) | All FR |
| NFR11 | Security | Passwords for EZShop accounts should not be directly saved | FR5 |


# Table of rights

|  Actor   | FR1         | FR2 | FR3 | FR4 | FR5 | 
| :---:    | :---------: | :---: | :---: | :---: | :---: |
| Cashier | X | | | | |
| Shop owner | X | X | X | X | X | 
| Logistic operator | | X | X | |   |
| Cash station | | | | X | |
| Pos station | | | | | |
| Barcode scanner | | | | | | 
| Receipt printer | | | | | |

# Use case diagram and use cases

## Use case brief
|  UC name   | Goal         | Description |
| :---:    | :---------: | :---: |
|          |             |       |



## Use case diagram

\<define here UML Use case diagram UCD summarizing all use cases, and their relationships>

\<next describe here each use case in the UCD>

### Use case 1, UC1

| Actors Involved  |                                                                      |
| :--------------: | :------------------------------------------------------------------: |
|   Precondition   | \<Boolean expression, must evaluate to true before the UC can start> |
|  Post condition  |  \<Boolean expression, must evaluate to true after UC is finished>   |
| Nominal Scenario |         \<Textual description of actions executed by the UC>         |
|     Variants     |                      \<other normal executions>                      |
|    Exceptions    |                        \<exceptions, errors >                        |

##### Scenario 1.1

\<describe here scenarios instances of UC1>

\<a scenario is a sequence of steps that corresponds to a particular execution of one use case>

\<a scenario is a more formal description of a story>

\<only relevant scenarios should be described>

|  Scenario 1.1  |                                                                            |
| :------------: | :------------------------------------------------------------------------: |
|  Precondition  | \<Boolean expression, must evaluate to true before the scenario can start> |
| Post condition |  \<Boolean expression, must evaluate to true after scenario is finished>   |


Steps

|     Actor's action      |  System action                                                                    | FR needed |
| :------------: | :------------------------------------------------------------------------: |:---:|
|               |                                                                 |  |
|   |  |  |
##### Scenario 1.2

##### Scenario 1.x

### Use case 2, UC2

..

### Use case x, UCx

..

# Glossary

\<use UML class diagram to define important terms, or concepts in the domain of the application, and their relationships>

\<concepts must be used consistently all over the document, ex in use cases, requirements etc>

# System Design

\<describe here system design>

\<must be consistent with Context diagram>

# Hardware Software architecture

\<describe here the hardware software architecture using UML deployment diagram >
