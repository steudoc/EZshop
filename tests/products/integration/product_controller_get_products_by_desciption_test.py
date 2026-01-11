import asyncio
import pytest
import pytest_asyncio
from typing import List
from app.database.database import AsyncSessionLocal, init_db, reset_db, AsyncSession
from app.controllers.product_controller import ProductController
from app.models.DTO.product_dto import ProductDTO
# CRITICAL: Import DAO to register the table in SQLAlchemy
from app.models.DAO.product_dao import ProductDAO

# --- INFRASTRUCTURE FIXTURES ---

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
def setup_database(event_loop):
    async def _reset():
        await reset_db()
        await init_db()
    event_loop.run_until_complete(_reset())

async def _get_session() -> AsyncSession:
    return AsyncSessionLocal()

# --- DATA FIXTURE ---

@pytest_asyncio.fixture
async def product_inventory():
    """
    Inserts 3 products into the DB to test search capabilities.
    1. Apple iPhone
    2. Samsung Galaxy
    3. Apple Watch
    """
    async with await _get_session() as session:
        products = [
            ProductDAO(
                barcode="1234567890128", 
                price_per_unit=999.0, 
                description="Apple iPhone 13", # Contains 'Apple' and 'iPhone'
                quantity=10, 
                position="1-A-1",
                involvedOperations=0
            ),
            ProductDAO(
                barcode="4006381333931", 
                price_per_unit=899.0, 
                description="Samsung Galaxy S21", # Contains 'Samsung'
                quantity=5, 
                position="1-A-2",
                involvedOperations=0
            ),
            ProductDAO(
                barcode="5012345678900", 
                price_per_unit=299.0, 
                description="Apple Watch Series 7", # Contains 'Apple'
                quantity=15, 
                position="1-A-3",
                involvedOperations=0
            )
        ]
        session.add_all(products)
        await session.commit()
        return products

# --- TEST CASES FOR GET_PRODUCTS_BY_DESCRIPTION ---

@pytest.mark.asyncio
async def test_search_by_description_partial_match(product_inventory):
    """
    Test finding products with a partial string.
    Search 'Apple' -> Should find 'Apple iPhone 13' and 'Apple Watch Series 7'
    """
    controller = ProductController()

    results = await controller.get_products_by_description("Apple")

    assert len(results) == 2
    # Verify descriptions contain the search term
    assert any(p.description == "Apple iPhone 13" for p in results)
    assert any(p.description == "Apple Watch Series 7" for p in results)

@pytest.mark.asyncio
async def test_search_by_description_case_insensitive(product_inventory):
    """
    Test that the search ignores case.
    Search 'samsung' (lowercase) -> Should find 'Samsung Galaxy S21'
    """
    controller = ProductController()

    # The DB has "Samsung", we search "samsung"
    results = await controller.get_products_by_description("samsung")

    assert len(results) == 1
    assert results[0].description == "Samsung Galaxy S21"
    assert results[0].barcode == "4006381333931"

@pytest.mark.asyncio
async def test_search_by_description_no_match(product_inventory):
    """
    Test searching for a string that appears in no product.
    """
    controller = ProductController()

    results = await controller.get_products_by_description("Nokia")

    assert isinstance(results, list)
    assert len(results) == 0

@pytest.mark.asyncio
async def test_search_by_description_empty_db():
    """
    Test searching when the database is empty.
    """
    # Note: We do NOT use the product_inventory fixture here, so DB is empty
    controller = ProductController()

    results = await controller.get_products_by_description("Any")

    assert len(results) == 0