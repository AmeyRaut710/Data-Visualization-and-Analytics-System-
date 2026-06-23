import pandas as pd
df = pd.DataFrame(columns=['A', 'B'])
outlier_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
try:
    res = outlier_mask.apply(lambda row: row.index[row].tolist(), axis=1).values
    print("Success empty df:", res)
except Exception as e:
    import traceback
    traceback.print_exc()

df2 = pd.DataFrame({'A': ['foo', 'bar'], 'B': ['baz', 'qux']})
outlier_mask2 = pd.DataFrame(False, index=df2.index, columns=df2.columns)
try:
    res2 = outlier_mask2.apply(lambda row: row.index[row].tolist(), axis=1).values
    print("Success 2 rows:", res2)
except Exception as e:
    import traceback
    traceback.print_exc()
