import os
os.environ["TESTING"] = "1"  # testing run
print(">>> Setting test DB environment:")

# Import application components AFTER setting env
from app.database import database
import pytest
import asyncio

@pytest.fixture(scope="session")
async def setup_test_db():
    # Initialize only the test DB in memory
    await database.init_db()
    yield
    # Optional teardown
    await database.reset_db()