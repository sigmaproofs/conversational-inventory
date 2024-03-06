import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scheme import Inventory

# Read data from the JSON file
with open('sample-data.json', 'r') as file:
    data = json.load(file)

# Create an engine to connect to your database
engine = create_engine('postgresql://doruk:doruk@localhost:5432/available_inventory')

# Create a session maker
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

# Add sample data to the session
for item in data:
    new_item = Inventory(
        sku=item['sku'],
        product_name=item['product_name'],
        quantity=item['quantity'],
        price=item['price'],
        size=item['size'],
        color=item['color'],
        brand=item['brand'],
        image=item['image'],
        description=item['description']
    )
    session.add(new_item)

# Commit the changes to persist them in the database
session.commit()

# Close the session
session.close()
