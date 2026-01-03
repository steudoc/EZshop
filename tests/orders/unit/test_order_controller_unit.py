import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.controllers.order_controller import OrderController
from app.models.DAO.order_dao import OrderDAO
from app.models.DTO.order_dto import OrderDTO
from app.models.order_status import OrderStatus
from app.models.errors.bad_request import BadRequestError


@pytest.fixture
def mock_repo():
    """Create a mock repository"""
    return AsyncMock()


@pytest.fixture
def controller_with_mock_repo(mock_repo):
    """Create a controller with mocked repository"""
    controller = OrderController()
    controller.repo = mock_repo
    return controller


class TestOrderControllerCreateIssuedOrder:
    """Test suite for create_issued_order method"""
    
    @pytest.mark.asyncio
    async def test_create_issued_order_success(self, controller_with_mock_repo, mock_repo):
        """Test successfully creating an issued order"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        result = await controller.create_issued_order(order_dto)
        
        assert isinstance(result, OrderDTO)
        assert result.product_barcode == "0000000001"
        assert result.quantity == 5
        assert result.status == OrderStatus.ISSUED
        mock_repo.create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_issued_order_sets_status(self, controller_with_mock_repo, mock_repo):
        """Test that status is set to ISSUED"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="TEST001",
            quantity=2,
            price_per_unit=5.0
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="TEST001",
            quantity=2,
            price_per_unit=5.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        await controller.create_issued_order(order_dto)
        
        # Verify status was set to ISSUED before calling repo
        assert order_dto.status == OrderStatus.ISSUED
    
    @pytest.mark.asyncio
    async def test_create_issued_order_zero_quantity_fails(self, controller_with_mock_repo):
        """Test that zero quantity raises error"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=0,
            price_per_unit=10.0
        )
        
        with pytest.raises(BadRequestError):
            await controller.create_issued_order(order_dto)
    
    @pytest.mark.asyncio
    async def test_create_issued_order_negative_quantity_fails(self, controller_with_mock_repo):
        """Test that negative quantity raises error"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=-5,
            price_per_unit=10.0
        )
        
        with pytest.raises(BadRequestError):
            await controller.create_issued_order(order_dto)
    
    @pytest.mark.asyncio
    async def test_create_issued_order_zero_price_fails(self, controller_with_mock_repo):
        """Test that zero price raises error"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=0.0
        )
        
        with pytest.raises(BadRequestError):
            await controller.create_issued_order(order_dto)
    
    @pytest.mark.asyncio
    async def test_create_issued_order_negative_price_fails(self, controller_with_mock_repo):
        """Test that negative price raises error"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=-10.0
        )
        
        with pytest.raises(BadRequestError):
            await controller.create_issued_order(order_dto)


class TestOrderControllerCreatePaidOrder:
    """Test suite for create_paid_order method"""
    
    @pytest.mark.asyncio
    async def test_create_paid_order_success(self, controller_with_mock_repo, mock_repo):
        """Test successfully creating a paid order"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        result = await controller.create_paid_order(order_dto)
        
        assert isinstance(result, OrderDTO)
        assert result.status == OrderStatus.PAID
        mock_repo.create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_paid_order_sets_status(self, controller_with_mock_repo, mock_repo):
        """Test that status is set to PAID"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="TEST001",
            quantity=3,
            price_per_unit=15.0
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="TEST001",
            quantity=3,
            price_per_unit=15.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        await controller.create_paid_order(order_dto)
        
        assert order_dto.status == OrderStatus.PAID
    
    @pytest.mark.asyncio
    async def test_create_paid_order_invalid_parameters_fails(self, controller_with_mock_repo):
        """Test that paid order with invalid params raises error"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=0,
            price_per_unit=10.0
        )
        
        with pytest.raises(BadRequestError):
            await controller.create_paid_order(order_dto)


class TestOrderControllerListOrders:
    """Test suite for list_orders method"""
    
    @pytest.mark.asyncio
    async def test_list_orders_success(self, controller_with_mock_repo, mock_repo):
        """Test successfully listing orders"""
        controller = controller_with_mock_repo
        order_dao1 = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        order_dao2 = OrderDAO(
            id=2,
            product_barcode="0000000002",
            quantity=3,
            price_per_unit=20.0,
            status=OrderStatus.PAID,
            issue_date=datetime.now()
        )
        mock_repo.list_orders = AsyncMock(return_value=[order_dao1, order_dao2])
        
        result = await controller.list_orders()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].product_barcode == "0000000001"
        assert result[1].product_barcode == "0000000002"
        mock_repo.list_orders.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_orders_empty(self, controller_with_mock_repo, mock_repo):
        """Test listing orders when none exist"""
        controller = controller_with_mock_repo
        mock_repo.list_orders = AsyncMock(return_value=[])
        
        result = await controller.list_orders()
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_list_orders_multiple(self, controller_with_mock_repo, mock_repo):
        """Test listing multiple orders"""
        controller = controller_with_mock_repo
        orders = [
            OrderDAO(id=i, product_barcode=f"BAR{i:010d}", quantity=i, 
                    price_per_unit=float(i*10), status=OrderStatus.ISSUED, issue_date=datetime.now())
            for i in range(1, 6)
        ]
        mock_repo.list_orders = AsyncMock(return_value=orders)
        
        result = await controller.list_orders()
        
        assert len(result) == 5
        assert all(isinstance(dto, OrderDTO) for dto in result)


class TestOrderControllerPayOrder:
    """Test suite for pay_order method"""
    
    @pytest.mark.asyncio
    async def test_pay_order_success(self, controller_with_mock_repo, mock_repo):
        """Test successfully paying an order"""
        controller = controller_with_mock_repo
        mock_repo.update_issued_order = AsyncMock()
        
        await controller.pay_order(order_id=1)
        
        mock_repo.update_issued_order.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_pay_order_invalid_id_not_int(self, controller_with_mock_repo):
        """Test that non-integer ID raises error"""
        controller = controller_with_mock_repo
        
        with pytest.raises(BadRequestError):
            await controller.pay_order(order_id="invalid")
    
    @pytest.mark.asyncio
    async def test_pay_order_negative_id_fails(self, controller_with_mock_repo):
        """Test that negative ID raises error"""
        controller = controller_with_mock_repo
        
        with pytest.raises(BadRequestError):
            await controller.pay_order(order_id=-1)
    
    """@pytest.mark.asyncio
    async def test_pay_order_zero_id_fails(self, controller_with_mock_repo):
        #Test that zero ID raises error
        controller = controller_with_mock_repo
        
        with pytest.raises(BadRequestError):
            await controller.pay_order(order_id=0)"""
    
    @pytest.mark.asyncio
    async def test_pay_order_multiple_valid_ids(self, controller_with_mock_repo, mock_repo):
        """Test paying multiple orders"""
        controller = controller_with_mock_repo
        mock_repo.update_issued_order = AsyncMock()
        
        for order_id in [1, 2, 3, 5, 100]:
            await controller.pay_order(order_id=order_id)
        
        assert mock_repo.update_issued_order.call_count == 5


class TestOrderControllerCompleteOrder:
    """Test suite for complete_order method"""
    
    @pytest.mark.asyncio
    async def test_complete_order_success(self, controller_with_mock_repo, mock_repo):
        """Test successfully completing an order"""
        controller = controller_with_mock_repo
        mock_repo.update_paid_order = AsyncMock()
        
        await controller.complete_order(order_id=1)
        
        mock_repo.update_paid_order.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_complete_order_invalid_id_not_int(self, controller_with_mock_repo):
        """Test that non-integer ID raises error"""
        controller = controller_with_mock_repo
        
        with pytest.raises(BadRequestError):
            await controller.complete_order(order_id="not_int")
    
    @pytest.mark.asyncio
    async def test_complete_order_negative_id_fails(self, controller_with_mock_repo):
        """Test that negative ID raises error"""
        controller = controller_with_mock_repo
        
        with pytest.raises(BadRequestError):
            await controller.complete_order(order_id=-5)
    
    """@pytest.mark.asyncio
    async def test_complete_order_zero_id_fails(self, controller_with_mock_repo):
        #Test that zero ID raises error
        controller = controller_with_mock_repo
        
        with pytest.raises(BadRequestError):
            await controller.complete_order(order_id=0)"""
    
    @pytest.mark.asyncio
    async def test_complete_order_large_id(self, controller_with_mock_repo, mock_repo):
        """Test completing order with large ID"""
        controller = controller_with_mock_repo
        mock_repo.update_paid_order = AsyncMock()
        
        large_id = 999999
        await controller.complete_order(order_id=large_id)
        
        mock_repo.update_paid_order.assert_called_once_with(large_id)


class TestOrderControllerCreateOrderValidation:
    """Test suite for internal _create_order validation"""
    
    @pytest.mark.asyncio
    async def test_create_order_clears_id(self, controller_with_mock_repo, mock_repo):
        """Test that _create_order clears the ID"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            id=999,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        await controller._create_order(order_dto)
        
        # Verify ID was set to None before creating
        assert order_dto.id is None
    
    @pytest.mark.asyncio
    async def test_create_order_repo_called_with_correct_params(self, controller_with_mock_repo, mock_repo):
        """Test that repository is called with correct parameters"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="BAR123",
            quantity=10,
            price_per_unit=25.50,
            status=OrderStatus.ISSUED
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="BAR123",
            quantity=10,
            price_per_unit=25.50,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        await controller._create_order(order_dto)
        
        call_args = mock_repo.create_order.call_args
        assert call_args[0][0] is None  # id should be None
        assert call_args[0][1] == "BAR123"  # product_barcode
        assert call_args[0][2] == 10  # quantity
        assert call_args[0][3] == 25.50  # price_per_unit


class TestOrderControllerEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_order_with_very_small_price(self, controller_with_mock_repo, mock_repo):
        """Test order with very small price"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=1,
            price_per_unit=0.01
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=1,
            price_per_unit=0.01,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        result = await controller.create_issued_order(order_dto)
        
        assert result.price_per_unit == 0.01
    
    @pytest.mark.asyncio
    async def test_order_with_large_quantity(self, controller_with_mock_repo, mock_repo):
        """Test order with large quantity"""
        controller = controller_with_mock_repo
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=1000000,
            price_per_unit=10.0
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=1000000,
            price_per_unit=10.0,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        result = await controller.create_issued_order(order_dto)
        
        assert result.quantity == 1000000
    
    @pytest.mark.asyncio
    async def test_order_with_large_price(self, controller_with_mock_repo, mock_repo):
        """Test order with large price"""
        controller = controller_with_mock_repo
        large_price = 999999.99
        order_dto = OrderDTO(
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=large_price
        )
        
        order_dao = OrderDAO(
            id=1,
            product_barcode="0000000001",
            quantity=5,
            price_per_unit=large_price,
            status=OrderStatus.ISSUED,
            issue_date=datetime.now()
        )
        mock_repo.create_order = AsyncMock(return_value=order_dao)
        
        result = await controller.create_issued_order(order_dto)
        
        assert result.price_per_unit == large_price
