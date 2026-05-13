import pandas as pd
import glob
import os

csv_file = glob.glob('مختصر بوابة البلاغات .csv')[0]
df = pd.read_csv(csv_file)
print(f'Total records: {len(df)}')
unique_coords = df.drop_duplicates(subset=[df.columns[1], df.columns[2]]) # assuming columns 1 and 2 are X and Y
print(f'Unique records after dropping coordinate duplicates: {len(unique_coords)}')

# Let's correctly identify the X and Y columns
x_col = [col for col in df.columns if 'X' in col][0]
y_col = [col for col in df.columns if 'Y' in col][0]

unique_coords_correct = df.drop_duplicates(subset=[x_col, y_col])
print(f'Unique coordinates (correct): {len(unique_coords_correct)}')

print('Decimal places in X:')
print(df[x_col].astype(str).apply(lambda x: len(x.split('.')[1]) if '.' in x else 0).value_counts())
