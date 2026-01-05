import pytest
from unittest.mock import MagicMock, AsyncMock
from app.repositories.product_repository import ProductRepository
from app.models.DAO.product_dao import ProductDAO
from app.models.errors.bad_request import BadRequestError
from app.models.errors.conflict_error import ConflictError


@pytest.fixture
def mock_session():
    """
    Crea un mock della sessione del database per simulare SQLAlchemy.
    """
    session = MagicMock()
    
    # Gestione del Context Manager (async with session:)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    
    # Metodi asincroni
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    
    # Metodi sincroni
    session.add = MagicMock()
    
    return session

@pytest.fixture
def repository(mock_session):
    """
    Inizializza il repository con la sessione mockata.
    """
    repo = ProductRepository()
    # Iniettiamo il mock sovrascrivendo il metodo interno
    repo._get_session = AsyncMock(return_value=mock_session)
    
    # Mockiamo get_product_by_barcode perché create_product lo usa internamente.
    # Di base diciamo che non trova nulla (None), così i test di successo funzionano.
    repo.get_product_by_barcode = AsyncMock(return_value=None)
    
    return repo

# --- TEST CASES (Funzioni libere, senza 'self') ---

@pytest.mark.asyncio
async def test_list_products_populated(repository, mock_session):
    """
    Testa che restituisca una lista di prodotti quando ce ne sono nel DB.
    """
    # ARRANGE
    # Creiamo due prodotti finti
    prod1 = ProductDAO(id=1, barcode="123456789012", description="Prod 1")
    prod2 = ProductDAO(id=2, barcode="123456789013", description="Prod 2")
    expected_list = [prod1, prod2]

    # Mockiamo la catena di SQLAlchemy: result.scalars().all()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = expected_list
    
    # Colleghiamo il risultato alla sessione
    mock_session.execute.return_value = mock_result

    # ACT
    products = await repository.list_products()

    # ASSERT
    assert len(products) == 2
    assert products[0].barcode == "123456789012"
    assert products == expected_list
    
    
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_products_empty(repository, mock_session):
    """
    Testa che restituisca una lista vuota (e non None) se il DB è vuoto.
    """
    # ARRANGE
    mock_result = MagicMock()
    # Il DB restituisce una lista vuota
    mock_result.scalars.return_value.all.return_value = []
    
    mock_session.execute.return_value = mock_result

    # ACT
    products = await repository.list_products()

    # ASSERT
    assert isinstance(products, list)
    assert len(products) == 0
    assert products == []