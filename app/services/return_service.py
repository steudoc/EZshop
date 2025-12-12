"""Return service Module.
This module contains the ReturnService class which handles the business logic
for return operations, interacting with the ReturnRepository to perform CRUD operations.
"""

from app.models.DAO.return_dao import ReturnDAO
from app.models.errors.return_errors import PaymentFailedError


class ReturnService:

    def calculate_refund(return_tx: ReturnDAO) -> float:
        """
        Calculate the total refund amount for a return transaction.
        """
        if not return_tx.lines:
            return 0.0
        return sum(line.quantity * line.price_per_unit for line in return_tx.lines)






