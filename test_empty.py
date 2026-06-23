import pandas as pd
import numpy as np
df = pd.DataFrame({'A': ['foo', ' ', '', 'bar', np.nan]})
mask = pd.Series(False, index=df.index)
for col in df.columns:
    is_empty = df[col].notna() & df[col].astype(str).str.match(r'^\s*$')
    mask = mask | is_empty
print(df[~mask])
