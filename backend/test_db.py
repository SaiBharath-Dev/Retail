from sqlalchemy import create_engine, text
from config import SQLALCHEMY_DATABASE_URI

# Create an engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Connect and run a test query
with engine.connect() as connection:
    result = connection.execute(text("SELECT now()"))
    print("Database time:", result.fetchone()[0])
