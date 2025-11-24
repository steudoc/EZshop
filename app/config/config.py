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

ROUTES = {
    "V1_AUTH": APP_V1_BASE_URL + URL_AUTH,
    "V1_USERS": APP_V1_BASE_URL + URL_USERS,
    
    "V1_GENERAL": APP_V1_BASE_URL,
}

# App configuration
APP_PORT = int(os.getenv("PORT", 5000))
