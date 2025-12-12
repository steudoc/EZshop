from enum import Enum

class OrderStatus(str, Enum):
    ISSUED = "ISSUED"
    PAID = "PAID"
    COMPLETED = "COMPLETED"
