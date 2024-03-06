# from sqlalchemy import Column, Integer, String, Float, DateTime
# from sqlalchemy.orm import declarative_base

# Base = declarative_base()

# class Inventory(Base):
#     __tablename__ = 'inventory'

#     id = Column(Integer, primary_key=True)
#     sku = Column(String)
#     product_name = Column(String)
#     quantity = Column(Integer)
#     price = Column(Float)
#     size = Column(String)
#     color = Column(String)
#     brand = Column(String)
#     image = Column(String)
#     description = Column(String)


from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    sku = Column(String)
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    size = Column(String)
    color = Column(String)
    brand = Column(String)
    image = Column(String)
    description = Column(String)

def create_database():
    # Create an engine to connect to  database
    engine = create_engine('postgresql://doruk:doruk@localhost:5432/available_inventory')


    Base.metadata.create_all(engine)


    Session = sessionmaker(bind=engine)

    
    session = Session()

    # sample data
    sample_data = [
        Inventory(sku="SKU001", product_name="T-Shirt", quantity=20, price=159.99, size="M", color="Red", brand="Canada Goose", image="tshirt_image_url", description="Classic red t-shirt made from premium cotton fabric. Perfect for casual wear."),
        Inventory(sku="SKU002", product_name="Hoodie", quantity=15, price=299.99, size="L", color="Black", brand="Stone Island", image="hoodie_image_url", description="Black hoodie crafted with high-quality fleece material. Features a signature Stone Island logo patch on the sleeve.")
        
    ]
    session.add_all(sample_data)

    
    session.commit()

    
    session.close()

if __name__ == "__main__":
    create_database()
