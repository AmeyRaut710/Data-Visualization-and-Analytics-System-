import pandas as pd
import requests

# Create mock dataset
df = pd.DataFrame({
    'cat_col': ['Mumbai', 'mumbai', 'MUMBAI', 'Delhi', 'delhi'],
    'date_col': ['01/01/2025', '2025-01-01', 'Jan-01-2025', '2025-01-02', '12/12/2025'],
    'dup_1': [1, 2, 3, 4, 5],
    'dup_2': [1, 2, 3, 4, 5],
    'high_null': [None, None, None, None, 'Valid']
})
df.to_csv('mock.csv', index=False)

try:
    # Upload
    url = "http://localhost:8000/api/upload"
    with open('mock.csv', 'rb') as f:
        res = requests.post(url, files={'file': ('mock.csv', f, 'text/csv')})
    print("Upload Status:", res.status_code)
    
    if res.status_code == 200:
        session_id = res.json()['session_id']

        # Get Quality
        res = requests.get(f"http://localhost:8000/api/quality/{session_id}")
        quality = res.json()
        
        print("\n--- Detected Anomalies ---")
        anomalies = quality.get('anomalies', {})
        print("Duplicate Columns:", anomalies.get('duplicate_columns'))
        print("Inconsistent Categories:", anomalies.get('inconsistent_categories_cols'))
        print("Date Format Problems:", anomalies.get('date_format_problems_cols'))
        print("High Null Percentage Columns:", anomalies.get('high_null_cols'))
except Exception as e:
    print("Error:", e)
