import pandas as pd
df = pd.DataFrame(columns=['A', 'B'])
try:
    res = df.apply(lambda row: row.index[row].tolist(), axis=1).values
    print("Success:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
