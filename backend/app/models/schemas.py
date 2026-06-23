from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DatasetOverviewResponse(BaseModel):
    filename: str
    file_size_bytes: int
    num_rows: int
    num_columns: int
    columns: List[str]
    dtypes: Dict[str, str]
    numerical_columns: List[str]
    categorical_columns: List[str]
    date_columns: List[str]
    boolean_columns: List[str]

class DataQualityResponse(BaseModel):
    total_missing_values: int
    missing_values_per_column: Dict[str, int]
    missing_values_per_row: Dict[str, int] # Using string key for JSON serialization
    total_duplicate_rows: int
    duplicate_percentage: float
    outliers_count: int
    outlier_percentage: float
    affected_columns: List[str]
    completeness_score: float
    consistency_score: float
    overall_score: float
