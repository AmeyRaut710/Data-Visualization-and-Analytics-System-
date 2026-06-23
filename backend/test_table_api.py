import asyncio
from app.api.routes import get_table_data
from app.core.state import active_sessions
import pandas as pd
import uuid

async def test():
    sid = str(uuid.uuid4())
    df = pd.DataFrame({
        'A': ['foo', '  ', 'bar', ''],
        'B': [1.0, 2.0, 3.0, 4.0]
    })
    # simulate drop
    cleaned_df = df.drop([1, 3])
    
    active_sessions[sid] = {"raw": df, "cleaned": cleaned_df}
    
    try:
        res = await get_table_data(sid, dataset="cleaned")
        print("Success, rows:", res['total_rows'])
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
