from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

class Household(db.Model):
    """Household model representing customer demographic information"""
    __tablename__ = 'four_400_households'
    
    id = db.Column(db.Integer, primary_key=True)
    hshd_num = db.Column(db.Integer, unique=True, nullable=False, index=True)
    loyalty_flag = db.Column(db.String(20))
    age_range = db.Column(db.String(50))
    marital_status = db.Column(db.String(50))
    income_range = db.Column(db.String(50))
    homeowner_desc = db.Column(db.String(50))
    hshd_composition = db.Column(db.String(50))
    hshd_size = db.Column(db.String(10))
    children = db.Column(db.String(10))
    
    # Relationship - one household can have many transactions
    transactions = db.relationship('Transaction', backref='household', lazy=True)
    
    def __repr__(self):
        return f'<Household #{self.hshd_num}>'

class Product(db.Model):
    """Product model representing product information"""
    __tablename__ = 'four_400_products'
    
    product_num = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100))
    commodity = db.Column(db.String(100))
    brand_type = db.Column(db.String(100))
    natural_organic_flag = db.Column(db.String(1))
    
    # Relationship - one product can be in many transactions
    transactions = db.relationship('Transaction', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product #{self.product_num}: {self.commodity}>'

class Transaction(db.Model):
    """Transaction model representing purchase transactions"""
    __tablename__ = 'four_400_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    hshd_num = db.Column(db.Integer, db.ForeignKey('households.hshd_num'), index=True)
    basket_num = db.Column(db.Integer, index=True)
    purchase_date = db.Column(db.DateTime, index=True)
    product_num = db.Column(db.Integer, db.ForeignKey('products.product_num'), index=True)
    spend = db.Column(db.Float)
    units = db.Column(db.Integer)
    store_region = db.Column(db.String(50))
    week_num = db.Column(db.Integer)
    year = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Transaction: HH#{self.hshd_num}, Basket#{self.basket_num}, Product#{self.product_num}>'
    
    @property
    def formatted_date(self):
        """Return formatted date string"""
        if self.purchase_date:
            return self.purchase_date.strftime('%Y-%m-%d')
        return "N/A"
