from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from werkzeug.utils import secure_filename
from io import StringIO
import time
import threading
from sqlalchemy.exc import SQLAlchemyError
from flask import Response, jsonify
import csv
from flask import session, flash, redirect, url_for



# Create the Flask app
app = Flask(__name__, template_folder='../frontend/templates')

# Load configurations directly (not from models)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800 
app.secret_key = 'supersecretkey'  # Needed for flash messages


# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
db = SQLAlchemy(app)

# Create a global variable to track upload progress
upload_progress = {
    'status': 'idle',  # 'idle', 'in_progress', 'completed', 'error'
    'message': '',
    'households_progress': 0,
    'products_progress': 0,
    'transactions_progress': 0,
    'error': None
}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

VALID_USERS = {
    'harshita': {
        'password': 'yoyo',
        'email': 'gadhaha@mail.uc.edu'
    }
}

# Update your index route to handle login
@app.route('/', methods=['GET', 'POST'])
def index():
    # If user is already logged in, redirect to dashboard
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    # Process login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate credentials
        if username in VALID_USERS and VALID_USERS[username]['password'] == password:
            # Set session variables
            session['username'] = username
            session['email'] = VALID_USERS[username]['email']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    
    # Display login form
    return render_template('login.html')

# Add a logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Add login check decorator for protected routes
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
def dashboard():
    # Get data for the dashboard
    demographics = get_demographics_engagement()
    engagement = get_engagement_over_time()
    seasonal = get_seasonal_trends()
    brand_preferences = get_brand_preferences()
    top_products = get_top_products()
    category_spend = get_category_spend()
    avg_basket_size = get_avg_basket_size()
    monthly_revenue = get_monthly_revenue()

    # Create charts with Plotly
    fig_engagement = px.line(engagement, x='year', y='total_spent', title='Engagement Over Time')
    engagement_graph = pio.to_html(fig_engagement, full_html=False)

    fig_seasonal = px.bar(seasonal, x='month', y='total_spent', title='Seasonal Trends')
    seasonal_graph = pio.to_html(fig_seasonal, full_html=False)

    fig_brands = px.pie(brand_preferences, names='brand_ty', values='customer_count', title='Brand Preferences')
    brand_graph = pio.to_html(fig_brands, full_html=False)

    fig_top_products = px.bar(top_products, x='commodity', y='total_units', title='Top-Selling Products')
    top_products_graph = pio.to_html(fig_top_products, full_html=False)

    fig_category_spend = px.bar(category_spend, x='department', y='total_spend', title='Category Spend Distribution')
    category_spend_graph = pio.to_html(fig_category_spend, full_html=False)

    fig_avg_basket = px.bar(avg_basket_size, x='hshd_num', y='avg_units', title='Avg Basket Size per Household')
    avg_basket_graph = pio.to_html(fig_avg_basket, full_html=False)

    fig_monthly_rev = px.line(monthly_revenue, x='month', y='total_spend', title='Monthly Revenue Trends')
    monthly_revenue_graph = pio.to_html(fig_monthly_rev, full_html=False)

    demographics_table = demographics.to_html(classes='table table-striped')

    return render_template('dashboard.html', demographics_table=demographics_table,
                           engagement_graph=engagement_graph, seasonal_graph=seasonal_graph,
                           brand_graph=brand_graph, top_products_graph=top_products_graph,
                           category_spend_graph=category_spend_graph, avg_basket_graph=avg_basket_graph,
                           monthly_revenue_graph=monthly_revenue_graph)

@app.route('/check_columns')
def check_columns():
    try:
        trans_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'four_400_transactions'
            ORDER BY ordinal_position
        """)
        trans_columns = db.session.execute(trans_query).fetchall()

        prod_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'four_400_products'
            ORDER BY ordinal_position
        """)
        prod_columns = db.session.execute(prod_query).fetchall()

        sample_trans_row = db.session.execute(text("SELECT * FROM four_400_transactions LIMIT 1")).fetchone()
        sample_prod_row = db.session.execute(text("SELECT * FROM four_400_products LIMIT 1")).fetchone()

        # Convert Row objects to dictionaries
        sample_trans = dict(sample_trans_row._mapping) if sample_trans_row else {}
        sample_prod = dict(sample_prod_row._mapping) if sample_prod_row else {}
        
        # Convert any non-serializable objects to strings
        for key, value in sample_trans.items():
            if not isinstance(value, (int, float, str, bool, type(None))):
                sample_trans[key] = str(value)
        
        for key, value in sample_prod.items():
            if not isinstance(value, (int, float, str, bool, type(None))):
                sample_prod[key] = str(value)

        result = {
            'transaction_columns': [col[0] for col in trans_columns],
            'product_columns': [col[0] for col in prod_columns],
            'transaction_sample': sample_trans,
            'product_sample': sample_prod
        }

        return render_template('column_info.html', data=result)
    except Exception as e:
        return f"Error: {str(e)}"

def get_demographics_engagement():
    query = """
    SELECT hshd_composition, hh_size, income_range, children, COUNT(*) as customer_count
    FROM four_400_households
    GROUP BY hshd_composition, hh_size, income_range, children
    """
    return pd.read_sql(query, db.engine)

def get_engagement_over_time():
    query = """
    SELECT EXTRACT(YEAR FROM purchase_) AS year, SUM(spend) AS total_spent
    FROM four_400_transactions
    GROUP BY year, purchase_
    ORDER BY year
    """
    return pd.read_sql(query, db.engine)

def get_seasonal_trends():
    query = """
    SELECT EXTRACT(MONTH FROM purchase_) AS month, SUM(spend) AS total_spent
    FROM four_400_transactions
    GROUP BY month, purchase_
    ORDER BY month
    """
    return pd.read_sql(query, db.engine)

def get_brand_preferences():
    query = """
    SELECT p.brand_ty, COUNT(*) AS customer_count
    FROM four_400_transactions t
    JOIN four_400_products p ON t.product_num = p.product_num
    WHERE p.brand_ty IN ('PRIVATE', 'NATIONAL', 'ORGANIC')
    GROUP BY p.brand_ty
    """
    return pd.read_sql(query, db.engine)

def get_top_products():
    query = """
    SELECT p.COMMODITY, SUM(t.units) AS total_units
    FROM four_400_transactions t
    JOIN four_400_products p ON t.product_num = p.product_num
    GROUP BY p.COMMODITY
    ORDER BY total_units DESC
    LIMIT 10
    """
    return pd.read_sql(query, db.engine)

def get_category_spend():
    query = """
    SELECT p.department, SUM(t.spend) AS total_spend
    FROM four_400_transactions t
    JOIN four_400_products p ON t.product_num = p.product_num
    GROUP BY p.department
    ORDER BY total_spend DESC
    """
    return pd.read_sql(query, db.engine)

def get_avg_basket_size():
    query = """
    SELECT hshd_num, AVG(units) AS avg_units
    FROM four_400_transactions
    GROUP BY hshd_num
    ORDER BY avg_units DESC
    LIMIT 10
    """
    return pd.read_sql(query, db.engine)

def get_monthly_revenue():
    query = """
    SELECT DATE_TRUNC('month', purchase_) AS month, SUM(spend) AS total_spend
    FROM four_400_transactions
    GROUP BY month
    ORDER BY month
    """
    return pd.read_sql(query, db.engine)

@app.route('/data_pull', methods=['GET', 'POST'])
def data_pull():
    if request.method == 'POST':
        hshd_num = request.form.get('hshd_num', '10')
        query = text("""
        SELECT 
            t.hshd_num, 
            t.basket_num,   
            t.purchase_ as date,     
            p.department,                
            p.commodity,
            p.product_num,
            t.spend,                     
            t.units                      
        FROM four_400_transactions t
        JOIN four_400_products p ON t.product_num = p.product_num
        WHERE t.hshd_num = :hshd
        ORDER BY t.hshd_num, t.basket_num, t.purchase_, p.product_num, p.department, p.commodity;
        """)
        try:
            result_proxy = db.session.execute(query, {"hshd": hshd_num})
            # Convert SQLAlchemy ResultProxy to a list of dictionaries
            results = []
            for row in result_proxy:
                row_dict = {}
                for key in row._mapping:
                    # Convert timestamp objects to strings
                    if hasattr(row._mapping[key], 'isoformat'):
                        row_dict[key] = row._mapping[key].isoformat()
                    else:
                        row_dict[key] = row._mapping[key]
                results.append(row_dict)
            
            print(f"Query results count: {len(results) if results else 0}")
            return render_template('data_pull.html', results=results, hshd_num=hshd_num)
        except Exception as e:
            error_msg = str(e)
            print(f"Query error: {error_msg}")
            return render_template('data_pull.html', results=None, error=error_msg)

    return render_template('data_pull.html', results=None)

@app.route('/upload_data', methods=['GET', 'POST'])
def upload_data():
    """Route for uploading and loading new datasets with progress monitoring"""
    if request.method == 'POST':
        # Check if the files are in the request
        if 'transactions_file' not in request.files or \
           'households_file' not in request.files or \
           'products_file' not in request.files:
            flash('All three files are required', 'error')
            return redirect(request.url)
        
        transactions_file = request.files['transactions_file']
        households_file = request.files['households_file']
        products_file = request.files['products_file']
        
        # Check if files are selected
        if transactions_file.filename == '' or \
           households_file.filename == '' or \
           products_file.filename == '':
            flash('All three files must be selected', 'error')
            return redirect(request.url)
        
        # Check file types
        if not (allowed_file(transactions_file.filename) and 
                allowed_file(households_file.filename) and 
                allowed_file(products_file.filename)):
            flash('Files must be CSV format', 'error')
            return redirect(request.url)
        
        try:
            # Save files to upload folder with unique names to avoid conflicts
            timestamp = int(time.time())
            transactions_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{secure_filename(transactions_file.filename)}")
            households_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{secure_filename(households_file.filename)}")
            products_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{secure_filename(products_file.filename)}")
            
            transactions_file.save(transactions_path)
            households_file.save(households_path)
            products_file.save(products_path)
            
            # Start a background thread for loading data
            thread = threading.Thread(
                target=load_all_data_background,
                args=(transactions_path, households_path, products_path)
            )
            thread.daemon = True
            thread.start()
            
            flash('Files uploaded! Data is being processed in the background. This may take a few minutes.', 'info')
            return redirect(url_for('upload_status'))
        
        except Exception as e:
            flash(f'Error processing files: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('upload_data.html')

@app.route('/upload_status')
def upload_status():
    """Page to show the status of data upload"""
    return render_template('upload_status.html')

@app.route('/check_upload_progress')
def check_upload_progress():
    """API endpoint to check upload progress"""
    global upload_progress
    # Make a copy of the progress dictionary to avoid modification during serialization
    progress_copy = dict(upload_progress)
    return jsonify(progress_copy)

def load_all_data_background(transactions_path, households_path, products_path):
    """Background function to load all data files"""
    global upload_progress
    
    upload_progress = {
        'status': 'in_progress',
        'message': 'Starting data load...',
        'households_progress': 0,
        'products_progress': 0,
        'transactions_progress': 0,
        'error': None
    }
    
    try:
        # Process smaller files first
        upload_progress['message'] = 'Loading households data...'
        load_households_bulk(households_path)
        upload_progress['households_progress'] = 100
        
        upload_progress['message'] = 'Loading products data...'
        load_products_bulk(products_path)
        upload_progress['products_progress'] = 100
        
        # Process the large transactions file last
        upload_progress['message'] = 'Loading transactions data...'
        load_transactions_bulk(transactions_path)
        upload_progress['transactions_progress'] = 100
        
        upload_progress['status'] = 'completed'
        upload_progress['message'] = 'All data loaded successfully!'
        
        # Clean up the files
        try:
            os.remove(transactions_path)
            os.remove(households_path)
            os.remove(products_path)
        except:
            pass  # Ignore errors in file cleanup
            
    except Exception as e:
        upload_progress['status'] = 'error'
        upload_progress['error'] = str(e)
        upload_progress['message'] = f'Error: {str(e)}'

def count_csv_lines(file_path):
    """Count the number of lines in a CSV file efficiently"""
    with open(file_path, 'r') as f:
        # Read first 100 lines to determine average line length
        lines = []
        for _ in range(100):
            line = f.readline()
            if not line:
                break
            lines.append(line)
        
        if not lines:
            return 0
            
        avg_line_length = sum(len(line) for line in lines) / len(lines)
        
        # Get file size and estimate total lines
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        
        # Estimate total lines (excluding header)
        estimated_lines = int(file_size / avg_line_length) - 1
        
        return max(0, estimated_lines)  # Ensure non-negative

def load_transactions_incremental(file_path):
    """Load only new transactions that aren't already in the database"""
    try:
        # Check if the transactions table exists
        table_exists = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'four_400_transactions'
            )
        """)).scalar()
        
        # If table doesn't exist, create it
        if not table_exists:
            with db.engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE four_400_transactions (
                    hshd_num INT,
                    basket_num INT,
                    purchase_ TIMESTAMP,
                    product_num INT,
                    spend FLOAT,
                    units INT
                )
                """))
                conn.execute(text("CREATE INDEX idx_trans_hshd_num ON four_400_transactions (hshd_num)"))
                conn.execute(text("CREATE INDEX idx_trans_product_num ON four_400_transactions (product_num)"))
        
        # Create a temporary table for the new data
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS temp_transactions"))
            conn.execute(text("""
            CREATE TABLE temp_transactions (
                hshd_num INT,
                basket_num INT,
                purchase_ TIMESTAMP,
                product_num INT,
                spend FLOAT,
                units INT
            )
            """))
        
        # Process the file in chunks
        batch_size = 10000
        total_processed = 0
        total_new = 0
        
        for chunk in pd.read_csv(file_path, chunksize=batch_size):
            # Clean column names
            chunk.columns = [col.lower().strip() for col in chunk.columns]
            
            # Convert date column to datetime
            chunk['purchase_'] = pd.to_datetime(chunk['purchase_'])
            
            # Prepare data for bulk insert to temp table
            data = StringIO()
            chunk.to_csv(data, sep='\t', header=False, index=False)
            data.seek(0)
            
            # Execute COPY command for fast bulk insert to temp table
            raw_conn = db.engine.raw_connection()
            try:
                cursor = raw_conn.cursor()
                cursor.copy_from(
                    data,
                    'temp_transactions',
                    sep='\t',
                    null='',  # Handle empty values as NULL
                    columns=['hshd_num', 'basket_num', 'purchase_', 'product_num', 'spend', 'units']
                )
                raw_conn.commit()
                cursor.close()
            finally:
                raw_conn.close()
            
            # Update progress
            total_processed += len(chunk)
            global upload_progress
            upload_progress['transactions_progress'] = min(90, int((total_processed/500000)*100))  # Estimate
            upload_progress['message'] = f'Processing transactions... ({total_processed} processed)'
        
        # Insert only records that don't exist in the main table
        upload_progress['message'] = 'Finding new transactions...'
        with db.engine.begin() as conn:
            # Count new records before inserting
            new_count = conn.execute(text("""
                SELECT COUNT(*) FROM temp_transactions t
                WHERE NOT EXISTS (
                    SELECT 1 FROM four_400_transactions m
                    WHERE m.hshd_num = t.hshd_num
                    AND m.basket_num = t.basket_num
                    AND m.purchase_ = t.purchase_
                    AND m.product_num = t.product_num
                )
            """)).scalar()
            
            if new_count > 0:
                upload_progress['message'] = f'Adding {new_count} new transactions...'
                # Insert only the new records
                result = conn.execute(text("""
                    INSERT INTO four_400_transactions
                    SELECT t.* FROM temp_transactions t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM four_400_transactions m
                        WHERE m.hshd_num = t.hshd_num
                        AND m.basket_num = t.basket_num
                        AND m.purchase_ = t.purchase_
                        AND m.product_num = t.product_num
                    )
                """))
                total_new = new_count
        
        # Clean up
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS temp_transactions"))
        
        upload_progress['transactions_progress'] = 100
        print(f"Successfully processed {total_processed} transactions, added {total_new} new records")
        return total_new
    except Exception as e:
        print(f"Error loading transactions: {str(e)}")
        raise Exception(f"Error loading transactions data: {str(e)}")

def load_households_incremental(file_path):
    """Load only new households that aren't already in the database"""
    try:
        # Check if the households table exists
        table_exists = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'four_400_households'
            )
        """)).scalar()
        
        # If table doesn't exist, create it
        if not table_exists:
            with db.engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE four_400_households (
                    hshd_num INT PRIMARY KEY,
                    loyalty VARCHAR(100),
                    age_range VARCHAR(100),
                    marital VARCHAR(100),
                    income_range VARCHAR(100),
                    homeowner VARCHAR(100),
                    hshd_composition VARCHAR(100),
                    hh_size VARCHAR(100),
                    children VARCHAR(100)
                )
                """))
        
        # Read the household data
        df = pd.read_csv(file_path)
        df.columns = [col.lower().strip() for col in df.columns]
        df = df.fillna('')  # Fill missing values
        
        # Create a temporary table for the new data
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS temp_households"))
            conn.execute(text("""
            CREATE TABLE temp_households (
                hshd_num INT PRIMARY KEY,
                loyalty VARCHAR(100),
                age_range VARCHAR(100),
                marital VARCHAR(100),
                income_range VARCHAR(100),
                homeowner VARCHAR(100),
                hshd_composition VARCHAR(100),
                hh_size VARCHAR(100),
                children VARCHAR(100)
            )
            """))
        
        # Bulk insert to temp table
        data = StringIO()
        df.to_csv(data, sep='\t', header=False, index=False)
        data.seek(0)
        
        raw_conn = db.engine.raw_connection()
        try:
            cursor = raw_conn.cursor()
            cursor.copy_from(
                data,
                'temp_households',
                sep='\t',
                null='',
                columns=['hshd_num', 'loyalty', 'age_range', 'marital', 'income_range', 
                         'homeowner', 'hshd_composition', 'hh_size', 'children']
            )
            raw_conn.commit()
            cursor.close()
        finally:
            raw_conn.close()
        
        # Insert only records that don't exist in the main table
        upload_progress['message'] = 'Finding new households...'
        with db.engine.begin() as conn:
            # Count new records before inserting
            new_count = conn.execute(text("""
                SELECT COUNT(*) FROM temp_households t
                WHERE NOT EXISTS (
                    SELECT 1 FROM four_400_households m
                    WHERE m.hshd_num = t.hshd_num
                )
            """)).scalar()
            
            if new_count > 0:
                upload_progress['message'] = f'Adding {new_count} new households...'
                # Insert only the new records
                result = conn.execute(text("""
                    INSERT INTO four_400_households
                    SELECT t.* FROM temp_households t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM four_400_households m
                        WHERE m.hshd_num = t.hshd_num
                    )
                """))
            
            # Update existing records with new information
            update_count = conn.execute(text("""
                UPDATE four_400_households m
                SET 
                    loyalty = t.loyalty,
                    age_range = t.age_range,
                    marital = t.marital,
                    income_range = t.income_range,
                    homeowner = t.homeowner,
                    hshd_composition = t.hshd_composition,
                    hh_size = t.hh_size,
                    children = t.children
                FROM temp_households t
                WHERE m.hshd_num = t.hshd_num
                AND (
                    m.loyalty != t.loyalty OR
                    m.age_range != t.age_range OR
                    m.marital != t.marital OR
                    m.income_range != t.income_range OR
                    m.homeowner != t.homeowner OR
                    m.hshd_composition != t.hshd_composition OR
                    m.hh_size != t.hh_size OR
                    m.children != t.children
                )
            """)).rowcount
        
        # Clean up
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS temp_households"))
        
        upload_progress['households_progress'] = 100
        upload_progress['message'] = f'Household data processed: {new_count} new, {update_count} updated'
        print(f"Successfully processed {len(df)} household records: {new_count} new, {update_count} updated")
        return new_count
    except Exception as e:
        print(f"Error loading households: {str(e)}")
        raise Exception(f"Error loading households data: {str(e)}")

def load_products_incremental(file_path):
    """Load only new products that aren't already in the database"""
    try:
        # Check if the products table exists
        table_exists = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'four_400_products'
            )
        """)).scalar()
        
        # If table doesn't exist, create it
        if not table_exists:
            with db.engine.begin() as conn:
                conn.execute(text("""
                CREATE TABLE four_400_products (
                    product_num INT PRIMARY KEY,
                    department VARCHAR(100),
                    commodity VARCHAR(100),
                    brand_ty VARCHAR(100),
                    natural_organic_flag VARCHAR(100)
                )
                """))
                conn.execute(text("CREATE INDEX idx_prod_num ON four_400_products (product_num)"))
        
        # Read the product data
        df = pd.read_csv(file_path)
        df.columns = [col.lower().strip() for col in df.columns]
        df = df.fillna('')  # Fill missing values
        
        # Create a temporary table for the new data
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS temp_products"))
            conn.execute(text("""
            CREATE TABLE temp_products (
                product_num INT PRIMARY KEY,
                department VARCHAR(100),
                commodity VARCHAR(100),
                brand_ty VARCHAR(100),
                natural_organic_flag VARCHAR(100)
            )
            """))
        
        # Bulk insert to temp table
        data = StringIO()
        df.to_csv(data, sep='\t', header=False, index=False)
        data.seek(0)
        
        raw_conn = db.engine.raw_connection()
        try:
            cursor = raw_conn.cursor()
            cursor.copy_from(
                data,
                'temp_products',
                sep='\t',
                null='',
                columns=['product_num', 'department', 'commodity', 'brand_ty', 'natural_organic_flag']
            )
            raw_conn.commit()
            cursor.close()
        finally:
            raw_conn.close()
        
        # Insert only records that don't exist in the main table
        upload_progress['message'] = 'Finding new products...'
        with db.engine.begin() as conn:
            # Count new records before inserting
            new_count = conn.execute(text("""
                SELECT COUNT(*) FROM temp_products t
                WHERE NOT EXISTS (
                    SELECT 1 FROM four_400_products m
                    WHERE m.product_num = t.product_num
                )
            """)).scalar()
            
            if new_count > 0:
                upload_progress['message'] = f'Adding {new_count} new products...'
                # Insert only the new records
                result = conn.execute(text("""
                    INSERT INTO four_400_products
                    SELECT t.* FROM temp_products t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM four_400_products m
                        WHERE m.product_num = t.product_num
                    )
                """))
            
            # Update existing products with new information
            update_count = conn.execute(text("""
                UPDATE four_400_products m
                SET 
                    department = t.department,
                    commodity = t.commodity,
                    brand_ty = t.brand_ty,
                    natural_organic_flag = t.natural_organic_flag
                FROM temp_products t
                WHERE m.product_num = t.product_num
                AND (
                    m.department != t.department OR
                    m.commodity != t.commodity OR
                    m.brand_ty != t.brand_ty OR
                    m.natural_organic_flag != t.natural_organic_flag
                )
            """)).rowcount
        
        # Clean up
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS temp_products"))
        
        upload_progress['products_progress'] = 100
        upload_progress['message'] = f'Product data processed: {new_count} new, {update_count} updated'
        print(f"Successfully processed {len(df)} product records: {new_count} new, {update_count} updated")
        return new_count
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        raise Exception(f"Error loading products data: {str(e)}")

# Updated background function to use incremental loading
def load_all_data_background(transactions_path, households_path, products_path):
    """Background function to load data files incrementally"""
    global upload_progress
    
    upload_progress = {
        'status': 'in_progress',
        'message': 'Starting incremental data load...',
        'households_progress': 0,
        'products_progress': 0,
        'transactions_progress': 0,
        'error': None,
        'stats': {
            'new_households': 0,
            'new_products': 0,
            'new_transactions': 0
        },
        'start_time': time.time()
    }
    
    try:
        # Process smaller files first
        upload_progress['message'] = 'Processing households data...'
        new_households = load_households_incremental(households_path)
        upload_progress['stats']['new_households'] = new_households
        
        upload_progress['message'] = 'Processing products data...'
        new_products = load_products_incremental(products_path)
        upload_progress['stats']['new_products'] = new_products
        
        # Process the large transactions file last (this takes the most time)
        upload_progress['message'] = 'Processing transactions data...'
        new_transactions = load_transactions_incremental(transactions_path)
        upload_progress['stats']['new_transactions'] = new_transactions
        
        # Update indexes if new data was added
        if new_transactions > 0 or new_products > 0 or new_households > 0:
            upload_progress['message'] = 'Optimizing database indexes...'
            with db.engine.begin() as conn:
                # Ensure we have the right indexes for data pull queries
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_indexes 
                            WHERE indexname = 'idx_trans_sort' AND tablename = 'four_400_transactions'
                        ) THEN
                            CREATE INDEX idx_trans_sort ON four_400_transactions 
                            (hshd_num, basket_num, purchase_, product_num);
                        END IF;
                    END $$;
                """))
        
        upload_progress['status'] = 'completed'
        upload_progress['message'] = f'All data processed! Added {new_households} households, {new_products} products, {new_transactions} transactions'
        
        # Clean up the files
        try:
            os.remove(transactions_path)
            os.remove(households_path)
            os.remove(products_path)
        except Exception as e:
            print(f"Error removing files: {str(e)}")
            # Don't raise exception for file cleanup issues
            
    except Exception as e:
        upload_progress['status'] = 'error'
        upload_progress['error'] = str(e)
        upload_progress['message'] = f'Error: {str(e)}'
        print(f"Error in data loading process: {str(e)}")
if __name__ == '__main__':
    app.run(debug=True)
