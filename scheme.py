from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockInventory(Base):
    __tablename__ = 'stock_inventory'

    id = Column(Integer, primary_key=True)
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    size = Column(String)
    color = Column(String)
    brand = Column(String)
    image = Column(String)