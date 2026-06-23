import pandas as pd
df = pd.DataFrame(columns=['A', 'B']) # 0 rows, 2 columns
print("0 rows, 2 cols:", df.sum().sum())

df2 = pd.DataFrame(index=[0, 1]) # 2 rows, 0 columns
print("2 rows, 0 cols:", df2.sum().sum())
