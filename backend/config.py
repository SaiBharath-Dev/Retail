import os
from sqlalchemy import create_engine



DATABASE_URL = "cockroachdb://harshita:NFAvvRIAIO7JeAiXOJBaxw@hostname:26257/defaultdb"
engine = create_engine(DATABASE_URL)


# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Example: testing connection
with engine.connect() as connection:
    result = connection.execute("SELECT now()")
    print(result.fetchone())
