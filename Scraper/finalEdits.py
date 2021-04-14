import pandas as pd

df = pd.read_csv('../data/Site.csv')

l = df['product-code'].value_counts()
print(l)
# for i in range(len(df)):
#     cat = df['product-category'][i]
# 
#     cat = cat.replace(', ', '-')
#     cat = cat.replace('/ ', '-')
# 
#     df['product-category'][i] = cat
# 
#     df['product-code'][i] = df['product-code'][i].strip()
#     df['product-category'][i] = df['product-category'][i].strip()
#     df['ProductName'][i] = df['ProductName'][i].strip()
#     df['your-price'][i] = df['your-price'][i].strip()
# 
#     try:
#         df['brand'][i] = df['brand'][i].strip()
#     except AttributeError as e:
#         print(e)
#         print(df['product-code'][i], df['brand'][i])
#     df['ImageURL'][i] = df['ImageURL'][i].strip()
# 
# df.to_csv('EAutoTools.csv', index=False)
