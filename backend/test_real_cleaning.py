import asyncio
from app.api.routes import get_table_data
from app.core.state import active_sessions
import pandas as pd
import numpy as np
import uuid

async def test():
    sid = str(uuid.uuid4())
    df = pd.DataFrame({
        'A': ['foo', '  ', 'bar', ''],
        'B': [1.0, 2.0, 3.0, 4.0]
    })
    
    # 1. Cleaned df where rows are dropped
    cleaned_df = df.drop([1, 3])
    
    active_sessions[sid] = {"raw": df, "cleaned": cleaned_df}
    
    try:
        res = await get_table_data(sid, dataset="cleaned")
        print("Success for dropped rows")
    except Exception as e:
        print("Error for dropped rows:", e)
        import traceback
        traceback.print_exc()

    # 2. Cleaned df where empty strings are replaced with nan and then dropped
    df2 = pd.DataFrame({'A': ['foo', '  ', 'bar', ''], 'B': [1.0, 2.0, 3.0, 4.0]})
    mask = pd.Series(False, index=df2.index)
    is_empty_str = df2['A'].notna() & df2['A'].astype(str).str.match(r'^\s*$')
    mask = mask | is_empty_str
    cleaned_df2 = df2[~mask]
    
    sid2 = str(uuid.uuid4())
    active_sessions[sid2] = {"raw": df2, "cleaned": cleaned_df2}
    
    try:
        res2 = await get_table_data(sid2, dataset="cleaned")
        print("Success for real cleaning logic")
    except Exception as e:
        print("Error for real cleaning logic:", e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
