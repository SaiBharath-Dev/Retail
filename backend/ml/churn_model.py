import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Load data
df = pd.read_csv('../../data/400_transactions.csv')

# Convert dates
df['date'] = pd.to_datetime(df['date'])

# Find last purchase date per household
last_purchase = df.groupby('HSHD_NUM')['date'].max().reset_index()
last_purchase.columns = ['HSHD_NUM', 'LastPurchaseDate']

# Assume the current date is the latest in data
current_date = df['date'].max()

# Calculate "days since last purchase"
last_purchase['DaysSinceLastPurchase'] = (current_date - last_purchase['LastPurchaseDate']).dt.days

# Define churn: 1 if more than 90 days without purchase
last_purchase['Churn'] = last_purchase['DaysSinceLastPurchase'].apply(lambda x: 1 if x > 90 else 0)

# Create some simple features
features = df.groupby('HSHD_NUM').agg({
    'SPEND': 'sum',
    'BASKET_NUM': 'nunique',
    'UNITS': 'sum'
}).reset_index()

# Merge features with churn label
data = pd.merge(features, last_purchase[['HSHD_NUM', 'Churn']], on='HSHD_NUM')

# Train model
X = data[['SPEND', 'BASKET_NUM', 'UNITS']]
y = data['Churn']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print(classification_report(y_test, y_pred))
