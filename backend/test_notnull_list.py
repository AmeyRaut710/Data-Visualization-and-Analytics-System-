import pandas as pd
df = pd.DataFrame({'A': [[1, 2], []]})
try:
    print(pd.notnull(df))
except Exception as e:
    import traceback
    traceback.print_exc()
