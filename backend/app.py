from flask import Flask, render_template, request
from models import db, Household, Transaction, Product
import pandas as pd

app = Flask(__name__, template_folder='../frontend/templates')
app.config.from_pyfile('config.py')
db.init_app(app)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/data_pull', methods=['GET', 'POST'])
def data_pull():
    if request.method == 'POST':
        hshd = request.form['hshd_num']
        results = db.session.execute("""
        SELECT t.hshd_num, t.basket_num, t.date, t.product_num,
               p.department, p.commodity, t.spend, t.units
        FROM transactions t
        JOIN products p ON t.product_num = p.product_num
        WHERE t.hshd_num = :hshd
        ORDER BY t.hshd_num, t.basket_num, t.date, t.product_num
        """, {'hshd': hshd})
        return render_template('data_pull.html', results=results)
    return render_template('data_pull.html', results=None)

if __name__ == '__main__':
    app.run(debug=True)
