from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Household(db.Model):
    __tablename__ = 'households'
    id = db.Column(db.Integer, primary_key=True)
    hshd_num = db.Column(db.Integer, unique=True)
    loyalty_flag = db.Column(db.String)

class Product(db.Model):
    __tablename__ = 'products'
    product_num = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String)
    commodity = db.Column(db.String)
    brand_type = db.Column(db.String)
    natural_organic_flag = db.Column(db.String)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    hshd_num = db.Column(db.Integer)
    basket_num = db.Column(db.Integer)
    product_num = db.Column(db.Integer)
    spend = db.Column(db.Float)
    units = db.Column(db.Integer)
    date = db.Column(db.String)
