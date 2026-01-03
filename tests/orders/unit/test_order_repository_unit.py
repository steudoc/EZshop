from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from datetime import datetime
from app.models.DAO.order_dao import OrderDAO
from app.models.DAO.product_dao import ProductDAO
from app.models.order_status import OrderStatus
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.system_repository import SystemRepository
from app.models.errors.notfound_error import NotFoundError
from app.models.errors.balance_error import BalanceError


@pytest.fixture
def mock_session():
    """Create a properly configured mock session"""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_repo(mock_session):
    """Create a repository with mocked session context manager"""
    repo = OrderRepository()
    
    # Create a mock context manager that returns mock_session
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    
    # get_session() should return the context manager
    repo.get_session = MagicMock(return_value=mock_context_manager)
    
    # Store context manager for test verification
    repo._mock_context_manager = mock_context_manager
    
    # Mock ProductRepository and SystemRepository
    repo._mock_product_repo = MagicMock(spec=ProductRepository)
    repo._mock_product_repo.get_product_by_barcode = AsyncMock()
    repo._mock_product_repo.include_product_in_op = AsyncMock()
    
    repo._mock_system_repo = MagicMock(spec=SystemRepository)
    repo._mock_system_repo.get_last_system_info = AsyncMock()
    repo._mock_system_repo.create_system_info = AsyncMock()
    
    return repo


class TestOrderRepositoryCreateOrder:
    """Test suite for create_order method"""
    
    @pytest.mark.asyncio
    async def test_create_issued_order_success(self, mock_repo, mock_session):
        """Test successfully creating an issued order"""
        # Mock product repository
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0)
        
        # Setup product repository mock
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        # Patch ProductRepository and SystemRepository in the module
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                result = await mock_repo.create_order(
                    id=None,
                    product_barcode="0000000001",
                    quantity=5,
                    price_per_unit=10.0,
                    status=OrderStatus.ISSUED,
                    issue_date=datetime.now()
                )
                
                assert isinstance(result, OrderDAO)
                assert result.product_barcode == "0000000001"
                assert result.quantity == 5
                assert result.status == OrderStatus.ISSUED
    
    @pytest.mark.asyncio
    async def test_create_order_adds_to_session(self, mock_repo, mock_session):
        """Test that order is added to session"""
        # Setup mocks
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=15.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                result = await mock_repo.create_order(
                    id=None,
                    product_barcode="0000000001",
                    quantity=3,
                    price_per_unit=15.0,
                    status=OrderStatus.ISSUED,
                    issue_date=datetime.now()
                )
                
                # Verify add was called
                mock_session.add.assert_called_once()
                added_object = mock_session.add.call_args[0][0]
                assert isinstance(added_object, OrderDAO)
    
    @pytest.mark.asyncio
    async def test_create_order_flushes_and_refreshes(self, mock_repo, mock_session):
        """Test that flush and refresh are called"""
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=20.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                result = await mock_repo.create_order(
                    id=None,
                    product_barcode="0000000001",
                    quantity=2,
                    price_per_unit=20.0,
                    status=OrderStatus.ISSUED,
                    issue_date=datetime.now()
                )
                
                # Verify flush and refresh were called
                mock_session.flush.assert_awaited_once()
                mock_session.refresh.assert_awaited_once()


class TestOrderRepositoryListOrders:
    """Test suite for list_orders method"""
    
    @pytest.mark.asyncio
    async def test_list_orders_success(self, mock_repo, mock_session):
        """Test successfully listing orders"""
        order1 = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        order2 = OrderDAO(
            id=2,
            product_barcode="0000000002",
            quantity=3,
            price_per_unit=20.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        
        # Mock the execute result
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[order1, order2])
        mock_query = MagicMock()
        mock_query.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_query)
        
        result = await mock_repo.list_orders()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
    
    @pytest.mark.asyncio
    async def test_list_orders_empty(self, mock_repo, mock_session):
        """Test listing orders when none exist"""
        # Mock empty result
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_query = MagicMock()
        mock_query.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_query)
        
        result = await mock_repo.list_orders()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_list_orders_session_cleanup(self, mock_repo, mock_session):
        """Test that session is properly closed"""
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_query = MagicMock()
        mock_query.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_query)
        
        await mock_repo.list_orders()
        
        # Context manager should be properly used
        mock_repo._mock_context_manager.__aenter__.assert_called_once()
        mock_repo._mock_context_manager.__aexit__.assert_called_once()


class TestOrderRepositoryGetOrder:
    """Test suite for get_order method"""
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, mock_repo, mock_session):
        """Test successfully retrieving an order"""
        order = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_session.get = AsyncMock(return_value=order)
        
        result = await mock_repo.get_order(order_id=1)
        
        assert isinstance(result, OrderDAO)
        assert result.id == 1
        mock_session.get.assert_awaited_once_with(OrderDAO, 1)
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self, mock_repo, mock_session):
        """Test retrieving non-existent order"""
        mock_session.get = AsyncMock(return_value=None)
        
        result = await mock_repo.get_order(order_id=999)
        
        assert result is None


class TestOrderRepositoryOrderStatusTransitions:
    """Test suite for order status update methods"""
    
    @pytest.mark.asyncio
    async def test_update_issued_order_success(self, mock_repo, mock_session):
        """Test updating order from ISSUED to PAID"""
        order = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_session.get = AsyncMock(return_value=order)
        
        # Mock system info for balance check
        mock_system_info = MagicMock()
        mock_system_info.balance = 1000.0
        mock_repo._mock_system_repo.get_last_system_info = AsyncMock(return_value=mock_system_info)
        mock_repo._mock_system_repo.create_system_info = AsyncMock()
        
        # Patch SystemRepository in the module
        with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
            mock_sys_class.return_value = mock_repo._mock_system_repo
            
            # The method should update and flush
            await mock_repo.update_issued_order(order_id=1)
            
            mock_session.get.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_update_paid_order_success(self, mock_repo, mock_session):
        """Test updating order from PAID to COMPLETED"""
        order = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0, quantity=10, position="A-1-1")
        
        mock_session.get = AsyncMock(return_value=order)
        
        # Mock product repository
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.is_position_valid = MagicMock(return_value=True)
        mock_repo._mock_product_repo.update_product = AsyncMock()
        
        # Patch ProductRepository in the module
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            mock_prod_class.return_value = mock_repo._mock_product_repo
            
            # The method should update and flush
            await mock_repo.update_paid_order(order_id=1)
            
            mock_session.get.assert_awaited_once()


class TestOrderRepositorySessionManagement:
    """Test suite for session lifecycle management"""
    
    @pytest.mark.asyncio
    async def test_list_orders_session_lifecycle(self, mock_repo, mock_session):
        """Test proper session lifecycle in list_orders"""
        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[])
        mock_query = MagicMock()
        mock_query.scalars = MagicMock(return_value=mock_scalars)
        mock_session.execute = AsyncMock(return_value=mock_query)
        
        await mock_repo.list_orders()
        
        # Verify context manager was properly used
        mock_repo._mock_context_manager.__aenter__.assert_called_once()
        mock_repo._mock_context_manager.__aexit__.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_order_session_lifecycle(self, mock_repo, mock_session):
        """Test proper session lifecycle in create_order"""
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                await mock_repo.create_order(
                    id=None,
                    product_barcode="0000000001",
                    quantity=5,
                    price_per_unit=10.0,
                    status=OrderStatus.ISSUED,
                    issue_date=datetime.now()
                )
                
                # Verify context manager was properly used
                mock_repo._mock_context_manager.__aenter__.assert_called_once()
                mock_repo._mock_context_manager.__aexit__.assert_called_once()


class TestOrderRepositoryOrderCreationVariations:
    """Test suite for order creation with various parameters"""
    
    @pytest.mark.asyncio
    async def test_create_order_with_different_statuses(self, mock_repo, mock_session):
        """Test creating orders with different statuses"""
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        # Mock system info for PAID status
        mock_system_info = MagicMock()
        mock_system_info.balance = 1000.0
        mock_repo._mock_system_repo.get_last_system_info = AsyncMock(return_value=mock_system_info)
        mock_repo._mock_system_repo.create_system_info = AsyncMock()
        
        statuses = [OrderStatus.ISSUED, OrderStatus.PAID, OrderStatus.COMPLETED]
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                for status in statuses:
                    result = await mock_repo.create_order(
                        id=None,
                        product_barcode="0000000001",
                        quantity=5,
                        price_per_unit=10.0,
                        status=status,
                        issue_date=datetime.now()
                    )
                    
                    assert isinstance(result, OrderDAO)
    
    @pytest.mark.asyncio
    async def test_create_order_with_different_quantities(self, mock_repo, mock_session):
        """Test creating orders with various quantities"""
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        quantities = [1, 5, 100, 1000]
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                for qty in quantities:
                    result = await mock_repo.create_order(
                        id=None,
                        product_barcode="0000000001",
                        quantity=qty,
                        price_per_unit=10.0,
                        status=OrderStatus.ISSUED,
                        issue_date=datetime.now()
                    )
                    
                    assert isinstance(result, OrderDAO)
                    assert result.quantity == qty
    
    @pytest.mark.asyncio
    async def test_create_order_with_different_prices(self, mock_repo, mock_session):
        """Test creating orders with various prices"""
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        
        prices = [0.01, 5.50, 100.00, 999.99]
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                for price in prices:
                    result = await mock_repo.create_order(
                        id=None,
                        product_barcode="0000000001",
                        quantity=5,
                        price_per_unit=price,
                        status=OrderStatus.ISSUED,
                        issue_date=datetime.now()
                    )
                    
                    assert isinstance(result, OrderDAO)
                    assert result.price_per_unit == price


class TestOrderRepositoryErrorHandling:
    """Test suite for error handling"""
    
    @pytest.mark.asyncio
    async def test_create_order_database_error_propagates(self, mock_repo, mock_session):
        """Test that database errors are propagated"""
        mock_product = ProductDAO(id=1, barcode="0000000001", description="Test", price_per_unit=10.0)
        mock_repo._mock_product_repo.get_product_by_barcode = AsyncMock(return_value=mock_product)
        mock_repo._mock_product_repo.include_product_in_op = AsyncMock()
        mock_session.flush = AsyncMock(side_effect=Exception("DB Error"))
        
        with patch('app.repositories.order_repository.ProductRepository') as mock_prod_class:
            with patch('app.repositories.order_repository.SystemRepository') as mock_sys_class:
                mock_prod_class.return_value = mock_repo._mock_product_repo
                mock_sys_class.return_value = mock_repo._mock_system_repo
                
                with pytest.raises(Exception):
                    await mock_repo.create_order(
                        id=None,
                        product_barcode="0000000001",
                        quantity=5,
                        price_per_unit=10.0,
                        status=OrderStatus.ISSUED,
                        issue_date=datetime.now()
                    )
    
    @pytest.mark.asyncio
    async def test_list_orders_database_error_propagates(self, mock_repo, mock_session):
        """Test that database errors in list_orders are propagated"""
        mock_session.execute = AsyncMock(side_effect=Exception("Query Error"))
        
        with pytest.raises(Exception):
            await mock_repo.list_orders()
