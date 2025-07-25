from database import Base, engine
from model_folder.model import Staff, Supplier, Product, Category  # Add all your models

# This will create the tables in your PostgreSQL DB
Base.metadata.create_all(bind=engine)
