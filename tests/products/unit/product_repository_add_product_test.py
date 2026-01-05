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
async def test_add_product_success(repository, mock_session):
    # ARRANGE
    valid_barcode = "8002270014901" 
    price = 10.50
    desc = "New Product"
    qty = 50
    
    # Simuliamo che NON esistano duplicati (la query ritorna lista vuota)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    # ACT
    result = await repository.create_product(valid_barcode, price, desc, qty)

    # ASSERT
    assert isinstance(result, ProductDAO)
    assert result.barcode == valid_barcode
    
    # Verifica che session.add sia stato chiamato con l'oggetto giusto
    mock_session.add.assert_called_once()
    args, _ = mock_session.add.call_args
    assert args[0].description == desc
    
    # Verifica salvataggio
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_product_invalid_data(repository, mock_session):
    # ARRANGE
    invalid_barcode = "123" # Troppo corto
    
    # ACT & ASSERT
    # Deve lanciare eccezione (es. BadRequest)
    with pytest.raises(BadRequestError) as excinfo: 
        await repository.create_product(invalid_barcode, 10.0, "Desc", 5)
    
    # Verifica che NON abbia toccato il DB
    mock_session.add.assert_not_called()

@pytest.mark.asyncio
async def test_add_product_conflict(repository, mock_session):
    # ARRANGE
    barcode = "8002270014901"
    
    # Simuliamo che il prodotto esista già nel DB
    existing_product = ProductDAO(barcode=barcode)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [existing_product]
    mock_session.execute.return_value = mock_result

    # ACT & ASSERT
    # Deve lanciare eccezione (es. Conflict)
    with pytest.raises(ConflictError) as excinfo:
        await repository.create_product(barcode, 10.0, "Desc", 5)
        
    assert "already exists" in str(excinfo.value)
    mock_session.add.assert_not_called()