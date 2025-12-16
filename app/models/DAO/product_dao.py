from sqlalchemy import Column, Integer, String, Float
from app.database.database import Base


class ProductDAO(Base):
    __tablename__ = "products"

	# product uinque ID in the table
    id = Column(Integer, primary_key=True, autoincrement=True) 
    barcode = Column(String, nullable=False, unique=True)
    price_per_unit = Column(Float, nullable=False, default=0)
    quantity = Column(Integer, nullable=False, default=0)
    position = Column(String, nullable=False, default="")
    description = Column(String, nullable=False)
    note = Column(String, nullable=True)
    # used to track weather a product has been involved in any store operation such as sales, orders and returns
    # it specifically represents the number of operations in which product is involved
    involvedOperations = Column(Integer, nullable=False, default=0)
        



