import pytest
import pandas as pd
import numpy as np
from app.services.data_quality import DataQualityService

def test_missing_vs_empty_separation():
    # Construct a dataframe with very specific permutations of missing and empty
    df = pd.DataFrame({
        'mixed_col': [
            'NaN',     # Missing
            'NULL',    # Missing
            None,      # Missing
            'NA',      # Missing
            '',        # Empty
            '   ',     # Empty
            '\t',      # Empty
            ' \n ',    # Empty
            'Valid',   # Neither
            123        # Neither
        ]
    })
    
    # Run the quality analysis
    quality_report = DataQualityService.analyze_quality(df)
    metrics = quality_report['metrics']
    scores = quality_report['scores']
    
    # We expect exactly 4 Missing Values ('NaN', 'NULL', None, 'NA')
    assert metrics['total_missing_values'] == 4, f"Expected 4 missing, got {metrics['total_missing_values']}"
    
    # We expect exactly 4 Empty Cells ('', '   ', '\t', ' \n ')
    assert metrics['total_empty_cells'] == 4, f"Expected 4 empty, got {metrics['total_empty_cells']}"
    
    # Total Cells = 10
    # Missing = 4, Empty = 4. 
    # completeness = 100 - ((4+4) / 10 * 100) = 20.0
    assert scores['missing_pct'] == 40.0
    assert scores['empty_pct'] == 40.0
    assert scores['completeness'] == 20.0
