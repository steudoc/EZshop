import os
os.environ["TESTING"] = "1"  # testing run
print(">>> Setting test DB environment:")

# Import application components AFTER setting env
import app.database
import pytest
import asyncio

@pytest.fixture(scope="session")
async def setup_test_db():
    # Initialize only the test DB in memory
    await app.database.database.init_db()
    yield
    # Optional teardown
    await app.database.database.reset_db()