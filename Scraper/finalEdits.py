import pandas as pd
from tqdm import tqdm
df = pd.read_csv('../data/Sample.csv')

df.drop_duplicates(keep='first', inplace=True)
df.reset_index(drop=True, inplace=True)

print(df.isna().sum())

for i in tqdm(range(len(df))):

    cat = df['product-category'][i]
    df['product-category'][i] = cat

    df['product-code'][i] = df['product-code'][i].strip()

    df['ProductName'][i] = df['ProductName'][i].strip()
    df['your-price'][i] = df['your-price'][i].strip()

    try:
        df['product-category'][i] = df['product-category'][i].strip()
    except AttributeError as e:
        # print(e)
        print(df['product-code'][i], df['product-category'][i])
    try:
        df['brand'][i] = df['brand'][i].strip()
    except AttributeError as e:
        print(e)
        # print(df['product-code'][i], df['brand'][i])
    df['ImageURL'][i] = df['ImageURL'][i].strip()

df.to_csv('Sample.csv', index=False)
