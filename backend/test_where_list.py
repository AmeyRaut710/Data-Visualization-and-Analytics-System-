import pandas as pd
import numpy as np

df = pd.DataFrame({'A': [[1, 2], []], 'B': [1.0, np.nan]})
try:
    res = df.where(pd.notnull(df), None)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
