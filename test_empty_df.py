import pandas as pd
df = pd.DataFrame(index=[0, 3, 4], columns=[])
try:
    res = df.apply(lambda row: row.index[row].tolist(), axis=1).values
    print("Success:", res)
except Exception as e:
    print("Error:", e)
