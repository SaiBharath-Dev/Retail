from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# Initialize the database
db = SQLAlchemy(app)

# Test connection
with app.app_context():
    try:
        result = db.session.execute(text("SELECT now()")).fetchone()
        print(f"Database connection successful! Current time: {result[0]}")
        
        # Test if tables exist and have data
        try:
            households = db.session.execute(text("SELECT COUNT(*) FROM four_400_households")).fetchone()
            print(f"Households table exists with {households[0]} records")
        except Exception as e:
            print(f"Error accessing households table: {e}")
            
        try:
            products = db.session.execute(text("SELECT COUNT(*) FROM four_400_products")).fetchone()
            print(f"Products table exists with {products[0]} records")
        except Exception as e:
            print(f"Error accessing products table: {e}")
            
        try:
            transactions = db.session.execute(text("SELECT COUNT(*) FROM four_400_transactions")).fetchone()
            print(f"Transactions table exists with {transactions[0]} records")
        except Exception as e:
            print(f"Error accessing transactions table: {e}")
            
    except Exception as e:
        print(f"Database connection failed: {e}")
