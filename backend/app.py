from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

# Create the Flask app
app = Flask(__name__, template_folder='../frontend/templates')

# Load configurations directly (not from models)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# Initialize the database
db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/check_columns')
def check_columns():
    try:
        # Get column names for transactions table
        trans_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'four_400_transactions'
            ORDER BY ordinal_position
        """)
        trans_columns = db.session.execute(trans_query).fetchall()
        
        # Get column names for products table
        prod_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'four_400_products'
            ORDER BY ordinal_position
        """)
        prod_columns = db.session.execute(prod_query).fetchall()
        
        # Get a sample row from each table
        sample_trans = db.session.execute(text("SELECT * FROM four_400_transactions LIMIT 1")).fetchone()
        sample_prod = db.session.execute(text("SELECT * FROM four_400_products LIMIT 1")).fetchone()
        
        # Format results for easy viewing
        result = {
            'transaction_columns': [col[0] for col in trans_columns],
            'product_columns': [col[0] for col in prod_columns],
            'transaction_sample': dict(sample_trans._mapping) if sample_trans else {},
            'product_sample': dict(sample_prod._mapping) if sample_prod else {}
        }
        
        return render_template('column_info.html', data=result)
    except Exception as e:
        return f"Error: {str(e)}"
    
 

@app.route('/data_pull', methods=['GET', 'POST'])
def data_pull():
    if request.method == 'POST':
        hshd_num = request.form.get('hshd_num', '10')
        
        # This query needs to be updated with the actual column names
        # from your database after you view them with /check_columns
        query = text("""
        SELECT 
            t.hshd_num as hshd_num,  /* Replace with actual column name */
            t.basket_num as basket_num,   /* Replace with actual column name */
            t.purchase_ as date,     /* Replace with actual column name */
            p.department,                /* Replace with actual column name */
            p.commodity,                 /* Replace with actual column name */
            t.spend,                     /* Replace with actual column name */
            t.units                      /* Replace with actual column name */
        FROM four_400_transactions t
        JOIN four_400_products p ON t.basket_num = p.product_num  /* Replace with actual column names */
        WHERE t.hshd_num = :hshd  /* Replace with actual column name */
        ORDER BY t.hshd_num, t.basket_num, t.purchase_, t.product_num  /* Replace with actual column names */;
        """)
        
        try:
            results = db.session.execute(query, {"hshd": hshd_num}).fetchall()
            print(f"Query results count: {len(results) if results else 0}")
            return render_template('data_pull.html', results=results)
        except Exception as e:
            error_msg = str(e)
            print(f"Query error: {error_msg}")
            return render_template('data_pull.html', results=None, error=error_msg)
    
    return render_template('data_pull.html', results=None)
if __name__ == '__main__':
    app.run(debug=True)
