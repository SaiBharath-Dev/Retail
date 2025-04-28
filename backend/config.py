import os
from sqlalchemy import create_engine
from sqlalchemy import text



DATABASE_URL = "cockroachdb://harshita:NFAvvRIAIO7JeAiXOJBaxw@retaildb-10729.j77.aws-us-east-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require"
engine = create_engine(DATABASE_URL)


# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Example: testing connection
with engine.connect() as connection:

    result = connection.execute(text("SELECT now()"))

    print(result.fetchone())
