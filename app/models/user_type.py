from enum import Enum

class UserType(str, Enum):
    Administrator = "Administrator"
    Cashier = "Cashier"
    ShopManager = "ShopManager"
