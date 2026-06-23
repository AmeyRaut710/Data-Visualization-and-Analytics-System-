import pandas as pd
from typing import Dict

# In-memory storage for active sessions
# Keys: session_id (str), Values: pd.DataFrame
# In production, use Redis or similar caching layer.
active_sessions: Dict[str, pd.DataFrame] = {}
