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

# --- DATA FIXTURES ---

@pytest_asyncio.fixture
async def product_inventory():
    """
    Populates the database with a list of products.
    """
    async with await _get_session() as session:
        products = [
            ProductDAO(
                barcode="1234567890128", 
                price_per_unit=10.0, 
                description="Product A", 
                quantity=10, 
                position="1-A-1",
                involvedOperations=0
            ),
            ProductDAO(
                barcode="4006381333931", 
                price_per_unit=20.0, 
                description="Product B", 
                quantity=5, 
                position="1-A-2",
                involvedOperations=0
            ),
            ProductDAO(
                barcode="5012345678900", 
                price_per_unit=30.0, 
                description="Product C", 
                quantity=2, 
                position="1-A-3",
                involvedOperations=0
            )
        ]
        session.add_all(products)
        await session.commit()
        return products

# --- TEST CASES FOR LIST_PRODUCTS ---

@pytest.mark.asyncio
async def test_list_products_empty():
    """
    Test that an empty list is returned when the DB is empty.
    """
    controller = ProductController()

    result = await controller.list_products()

    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.asyncio
async def test_list_products_populated(product_inventory):
    """
    Test that all products in the DB are returned as DTOs.
    """
    controller = ProductController()

    result = await controller.list_products()

    # 1. Check count
    assert len(result) == 3

    # 2. Check types
    assert all(isinstance(p, ProductDTO) for p in result)

    # 3. Check content (Sort by barcode to ensure order for comparison)
    result.sort(key=lambda x: x.barcode)
    
    # Expected barcodes from fixture
    expected_barcodes = ["1234567890128", "4006381333931", "5012345678900"]
    result_barcodes = [p.barcode for p in result]
    
    assert result_barcodes == expected_barcodes
    assert result[0].description == "Product A"