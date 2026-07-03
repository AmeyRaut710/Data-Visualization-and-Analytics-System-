import time
import io
import polars as pl

from app.services.metadata_manager import MetadataManager

# Create a dummy CSV with 500k rows, 10 columns
print("Creating dummy dataset...")
rows = 500000
data = "id,age,name,salary,department,date,status,score,notes,is_active\n"
row = "1,25.5,A,50000,Engineering,2023-01-01,Active,95,good,true\n"
row2 = "2,,B,NULL,Sales,2023-01-02,Inactive,,bad,false\n"
row3 = "3,NaN,C, ,HR,2023-01-03,Active,88,,true\n"
row4 = "4, 30 ,D,60000,Engineering,2023-01-04,Active,100,ok,true\n"
row5 = "5,NULL,E,70000,Marketing,2023-01-05,,92,,false\n"
csv_bytes = (data + (row+row2+row3+row4+row5) * (rows // 5)).encode('utf-8')

print("Reading CSV...")
start = time.time()
df = pl.read_csv(io.BytesIO(csv_bytes), infer_schema_length=0)
print(f"Read time: {time.time() - start:.3f}s")

print("Computing masks...")
t0 = time.time()
cache, df_typed = MetadataManager.compute_all_masks(df)
t1 = time.time()

print(f"Masks calculation took: {t1 - t0:.3f}s")
print("Cache missing columns:", list(cache['missing_indices'].keys()))

# Profile Data Cleaning targeted update
from app.services.data_cleaning import DataCleaningService
print("Cleaning missing values...")
t2 = time.time()
df_cleaned = DataCleaningService._clean_missing_values(df_typed, ["age", "salary"], "Replace with Mean", None, cache)
t3 = time.time()
print(f"Clean missing values took: {t3 - t2:.3f}s")
