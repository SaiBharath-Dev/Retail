import pandas as pd
from models import db, Household, Transaction, Product

def load_households_data(file_path):
    """Load households data from CSV file to database"""
    try:
        df = pd.read_csv(file_path)
        print(f"Loading {len(df)} household records...")
        count = 0
        
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
            count += 1
            
            # Commit in batches to avoid memory issues
            if count % 1000 == 0:
                db.session.commit()
                print(f"Processed {count} household records...")
        
        db.session.commit()
        print(f"Successfully loaded {count} household records")
        return count
    except Exception as e:
        db.session.rollback()
        print(f"Error loading household data: {str(e)}")
        raise

def load_products_data(file_path):
    """Load products data from CSV file to database"""
    try:
        df = pd.read_csv(file_path)
        print(f"Loading {len(df)} product records...")
        count = 0
        
        for _, row in df.iterrows():
            product = Product(
                product_num=row['PRODUCT_NUM'],
                department=row.get('DEPARTMENT', ''),
                commodity=row.get('COMMODITY', ''),
                brand_type=row.get('BRAND_TYPE', ''),
                natural_organic_flag=row.get('NATURAL_ORGANIC_FLAG', '')
            )
            db.session.merge(product)  # Use merge to handle updates
            count += 1
            
            # Commit in batches to avoid memory issues
            if count % 1000 == 0:
                db.session.commit()
                print(f"Processed {count} product records...")
        
        db.session.commit()
        print(f"Successfully loaded {count} product records")
        return count
    except Exception as e:
        db.session.rollback()
        print(f"Error loading product data: {str(e)}")
        raise

