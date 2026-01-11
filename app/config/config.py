import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Detect testing mode
IS_TEST = os.getenv("TESTING", "0") == "1"
# Database
if IS_TEST:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
else:
    DB_FILE_PATH = DATA_DIR / "database.sqlite"
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE_PATH}"

# JWT Configuration
TOKEN_LIFESPAN_HOURS = 24
SECRET_KEY = "b}2ZzqQ!eQ!t7rFeT[GHs6FZ+*L]2VqR{vnLn>4-V3[5W-V{f^"
ALGORITHM = "HS256"

# Application URLs
APP_V1_BASE_URL = "/api/v1"
URL_AUTH = "/auth"
URL_USERS = "/users"
URL_RETURNS = "/returns"
URL_BALANCE = "/balance"
URL_PRODUCTS= "/products"
URL_SALES= "/sales"
URL_ORDERS = "/orders"
URL_CUSTOMERS = "/customers"
URL_CARDS = "/cards"


ROUTES = {
    "V1_AUTH": APP_V1_BASE_URL + URL_AUTH,
    "V1_USERS": APP_V1_BASE_URL + URL_USERS,
    "V1_CUSTOMERS_CARDS" : APP_V1_BASE_URL+URL_CUSTOMERS+URL_CARDS,
    "V1_CUSTOMERS" : APP_V1_BASE_URL+URL_CUSTOMERS,
    "V1_RETURNS": APP_V1_BASE_URL + URL_RETURNS,
    "V1_BALANCE": APP_V1_BASE_URL + URL_BALANCE,
    "V1_PRODUCTS": APP_V1_BASE_URL + URL_PRODUCTS,
    "V1_SALES": APP_V1_BASE_URL + URL_SALES,
    "V1_ORDERS": APP_V1_BASE_URL + URL_ORDERS,
    "V1_GENERAL": APP_V1_BASE_URL,
}

# App configuration
APP_PORT = int(os.getenv("PORT", 5000))
