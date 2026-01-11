from enum import Enum

class SaleStatus(str, Enum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    PAID = "PAID"