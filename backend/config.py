import os
from sqlalchemy import create_engine

# Load database URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Example: testing connection
with engine.connect() as connection:
    result = connection.execute("SELECT now()")
    print(result.fetchone())
