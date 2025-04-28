import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

df = pd.read_csv('../../data/400_transactions.csv')
df['spend'] = df['SPEND']
grouped = df.groupby('HSHD_NUM').agg({'spend':'sum', 'BASKET_NUM':'nunique'}).reset_index()
grouped.columns = ['HSHD_NUM', 'TotalSpend', 'NumBaskets']

X = grouped[['NumBaskets']]
y = grouped['TotalSpend']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = LinearRegression()
model.fit(X_train, y_train)

print(f"Score: {model.score(X_test, y_test)}")
