import pandas as pd
from models import db, Household, Transaction, Product

def load_households_data(file_path):
    """Load households data from CSV file to database"""
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        household = Household(
            hshd_num=row['HSHD_NUM'],
            loyalty_flag=row.get('LOYALTY_FLAG', ''),
            age_range=row.get('AGE_RANGE', ''),
            marital_status=row.get('MARITAL_STATUS', ''),
            income_range=row.get('INCOME_RANGE', ''),
            homeowner_desc=row.get('HOMEOWNER_DESC', ''),
            hshd_composition=row.get('HSHD_COMPOSITION', ''),
            hshd_size=row.get('HSHD_SIZE', ''),
            children=row.get('CHILDREN', '')
        )
        db.session.merge(household)  # Use merge to handle updates
    db.session.commit()
    return len(df)

def load_products_data(file_path):
    """Load products data from CSV file to database"""
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        product = Product(
            product_num=row['PRODUCT_NUM'],
            department=row.get('DEPARTMENT', ''),
            commodity=row.get('COMMODITY', ''),
            brand_type=row.get('BRAND_TYPE', ''),
            natural_organic_flag=row.get('NATURAL_ORGANIC_FLAG', '')
        )
        db.session.merge(product)  # Use merge to handle updates
    db.session.commit()
    return len(df)

def load_transactions_data(file_path):
    """Load transactions data from CSV file to database"""
    df = pd.read_csv(file_path)
    # Convert date columns if needed
    if 'PURCHASE_DATE' in df.columns:
        df['PURCHASE_DATE'] = pd.to_datetime(df['PURCHASE_DATE'])
    
    for _, row in df.iterrows():
        transaction = Transaction(
            hshd_num=row['HSHD_NUM'],
            basket_num=row['BASKET_NUM'],
            purchase_date=row.get('PURCHASE_DATE', None),
            product_num=row['PRODUCT_NUM'],
            spend=row['SPEND'],
            units=row['UNITS'],
            store_region=row.get('STORE_REGION', ''),
            week_num=row.get('WEEK_NUM', 0),
            year=row.get('YEAR', 0)
        )
        db.session.add(transaction)
    
    db.session.commit()
    return len(df)
