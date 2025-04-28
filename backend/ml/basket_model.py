import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

# Load transactions
df = pd.read_csv('../../data/400_transactions.csv')

# Create basket data
basket = (df.groupby(['HSHD_NUM', 'BASKET_NUM', 'PRODUCT_NUM'])['PRODUCT_NUM']
          .count().unstack().reset_index().fillna(0)
          .set_index(['HSHD_NUM', 'BASKET_NUM']))

# Convert quantity to 1/0
basket = basket.applymap(lambda x: 1 if x > 0 else 0)

# Apply Apriori algorithm
frequent_itemsets = apriori(basket, min_support=0.01, use_colnames=True)

# Generate association rules
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)

# Save top rules
rules.to_csv('../../data/basket_rules.csv', index=False)

print("Top 5 Rules:")
print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head())
