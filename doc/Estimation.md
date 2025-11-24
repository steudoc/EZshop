# Project Estimation

Date:

Version:

# Estimation approach

Consider the EZShop project as described in your requirements document, assume that you are going to develop the project INDEPENDENT of the deadlines of the course, and from scratch

# Estimate by size

###

|                                                                                                         | Estimate |
| ------------------------------------------------------------------------------------------------------- | ------- |
| NC = Estimated number of classes to be developed                                                        |       30 |
| A = Estimated average size per class, in LOC                                                            |       70 |
| S = Estimated size of project, in LOC (= NC \* A)                                                       |     2100 |
| E = Estimated effort, in person hours (here use productivity 10 LOC per person hour)                    |      210 |
| C = Estimated cost, in euro (here use 1 person hour cost = 30 euro)                                     |     6300 |
| Estimated calendar time, in calendar weeks (Assume team of 5 people, 8 hours per day, 5 days per week ) |  1 week and 1 day |

# Estimate by product decomposition

###

| component name       | Estimated effort (person hours) |
| :------------------- | :------------------------------ |
| requirement document | 50 |
| design document      | 15 |
| GUI prototype        | 35 |
| EZshop application   | 217 (total) |
| &nbsp;&nbsp;&nbsp; GUI |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GUI structure design | 10 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tabs |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; login tab | 3 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; sale management tab(s) | 30 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; product inventory management tab(s) | 15 | 
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; orders management tab(s) | 10 | 
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; suppliers management tab(s)  | 6 | 
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; accounting tab(s)  | 15 | 
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; EZshop accounts management tab(s)  | 6 |
| &nbsp;&nbsp;&nbsp; backend |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; core module |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; low-level design | 30 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; source code | 50 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; DB management module |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; low-level design | 7 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; source code | 15 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GUI integration module |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; low-level design | 5 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; source code | 15 |
| database |  |
| &nbsp;&nbsp;&nbsp; schema definition document | 15 |
| &nbsp;&nbsp;&nbsp; DB tables | 15 |
| &nbsp;&nbsp;&nbsp; DB optimization structures | 5 |
| user guide | 15 |


Estimated duration: 2 weeks

# Estimate by activity decomposition + Gantt chart

###
step 1: activities (WBS), step 2 Gantt chart
| Activity name | Estimated effort (person hours) |
| ------------- | ------------------------------- |
| Requirements definition | |
| &nbsp;&nbsp;&nbsp; explore target market needs | 16 |
| &nbsp;&nbsp;&nbsp; define functional requirements | 29 |
| &nbsp;&nbsp;&nbsp; define non-functional requirements | 5 |
| Design | |
| &nbsp;&nbsp;&nbsp; redact system design document | 10 |
| &nbsp;&nbsp;&nbsp; GUI prototype | 35 |
| &nbsp;&nbsp;&nbsp; explore available development technologies| |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; choose programming language | 4 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; choose GUI framework | 8 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; choose database technology | 4 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; choose CM tool | 2 |
| Application developement| |
| &nbsp;&nbsp;&nbsp; software architecture definition | 20 |
| &nbsp;&nbsp;&nbsp; implementation| |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GUI creation| |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tabs creation | 60 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tabs documentation | 10 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; initial GUI validation | 25 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; source code creation| |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; coding | 100 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; testing | 10 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; documentation | 10 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; db creation| |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; db schema definition | 15 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; db schema documentation | 2 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; db implementation | 20 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; DB integration | 10 |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GUI integration | 10 |
| &nbsp;&nbsp;&nbsp; validation | 20 |
| &nbsp;&nbsp;&nbsp; final polish and bug-fixes | 18 |
| &nbsp;&nbsp;&nbsp; User guide development | 30 |


###

## Gantt chart

![Gantt chart for EZshop project](./images/EstimationGantt.png)

Estimated duration: 4 weeks

# Summary

Report here the results of the three estimation approaches. The estimates may differ. Discuss here the possible reasons for the difference

|                                    | Estimated effort (ph) | Estimated duration (calendar time, relative)|
| ---------------------------------- | ---------------- | ------------------ |
| estimate by size                   | 210 | 1 week and 1 day |
| estimate by product decomposition  | 367 | 2 weeks |
| estimate by activity decomposition (Gantt) | 473 | 4 weeks |


Notes:

Estimated project effort is low for size-estimation because it does not include any document or deliverable outside of code, while WBS has high estimated effort because it also includes activities that are needed but do not produce a deliverable.

The WBS decomposition with the gantt chart produces a longer calendar-time duration compared to the other estimation techniques because it considers dependencies between activities.