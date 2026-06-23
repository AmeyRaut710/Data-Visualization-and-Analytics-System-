import pandas as pd
import numpy as np

class MetadataManager:
    @staticmethod
    def compute_all_masks(df: pd.DataFrame) -> dict:
        global_dups = df.duplicated(keep=False)
        numerical_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
        outlier_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        
        if not numerical_cols.empty and len(df) > 10:
            for col in numerical_cols:
                col_str = str(col).lower()
                if 'id' in col_str or 'name' in col_str or 'phone' in col_str or 'zip' in col_str or 'year' in col_str:
                    continue
                    
                s = df[col].dropna()
                if len(s) < 10: continue
                
                method = 'IQR'
                is_large = len(s) > 50000
                skewness = s.skew()
                is_normal = pd.notna(skewness) and abs(skewness) < 0.5
                
                if is_large and is_normal:
                    method = 'Z-Score'
                    
                if method == 'IQR':
                    q1 = s.quantile(0.25)
                    q3 = s.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    mask = (df[col] < lower) | (df[col] > upper)
                else:
                    mean = s.mean()
                    std = s.std()
                    if std > 0:
                        mask = ((df[col] - mean) / std).abs() > 3
                    else:
                        mask = pd.Series(False, index=df.index)
                        
                outlier_mask[col] = mask.fillna(False)
                
        def is_empty_string(x):
            return isinstance(x, str) and str(x).strip() == ''
            
        empty_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        for col in df.columns:
            s = df[col]
            if isinstance(s, pd.DataFrame):
                for c in range(s.shape[1]):
                    empty_mask[col] = empty_mask[col] | s.iloc[:, c].map(is_empty_string)
            else:
                empty_mask[col] = s.map(is_empty_string)
                
        missing_mask = df.isna()
        
        invalid_type_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        inconsistent_cat_mask = pd.DataFrame(False, index=df.index, columns=df.columns)
        
        string_cols = df.select_dtypes(include=['object', 'string']).columns
        for col in string_cols:
            valid_pd = df[col].dropna()
            valid_pd = valid_pd[valid_pd.astype(str).str.strip() != ""]
            valid_count = len(valid_pd)
            if valid_count == 0: continue
            
            num_count = valid_pd.astype(str).str.contains(r'^-?\d+\.?\d*$', regex=True).sum()
            email_count = valid_pd.astype(str).str.contains(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', regex=True).sum()
            phone_count = valid_pd.astype(str).str.contains(r'^\+?[\d\s\-\(\)]{7,15}$', regex=True).sum()
            
            if num_count / valid_count > 0.8:
                invalid_type_mask[col] = df[col].notna() & (df[col].astype(str).str.strip() != "") & (~df[col].astype(str).str.contains(r'^-?\d+\.?\d*$', regex=True))
            elif email_count / valid_count > 0.8:
                invalid_type_mask[col] = df[col].notna() & (df[col].astype(str).str.strip() != "") & (~df[col].astype(str).str.contains(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', regex=True))
            elif phone_count / valid_count > 0.8:
                invalid_type_mask[col] = df[col].notna() & (df[col].astype(str).str.strip() != "") & (~df[col].astype(str).str.contains(r'^\+?[\d\s\-\(\)]{7,15}$', regex=True))
                
            original_uniques = valid_pd.nunique()
            if 0 < original_uniques < 1000:
                lower_pd = valid_pd.astype(str).str.lower()
                if lower_pd.nunique() < original_uniques:
                    counts = valid_pd.value_counts().reset_index()
                    counts.columns = ['val', 'count']
                    counts['lower'] = counts['val'].str.lower()
                    counts = counts.sort_values('count', ascending=False)
                    dominant_casing = counts.groupby('lower').first()['val']
                    
                    def is_inconsistent(x):
                        if pd.isna(x) or str(x).strip() == "": return False
                        return str(x) != dominant_casing.get(str(x).lower(), str(x))
                        
                    inconsistent_cat_mask[col] = df[col].map(is_inconsistent)

        return {
            "global_dups": global_dups,
            "outlier_mask": outlier_mask,
            "empty_mask": empty_mask,
            "missing_mask": missing_mask,
            "invalid_type_mask": invalid_type_mask,
            "inconsistent_cat_mask": inconsistent_cat_mask
        }

    @staticmethod
    def update_masks(df: pd.DataFrame, cache: dict, issue: str, columns: list) -> dict:
        # Instead of recalculating everything, we do a simple sync.
        # First, drop any rows that no longer exist in df from the masks
        for k in cache:
            if isinstance(cache[k], pd.Series):
                cache[k] = cache[k].reindex(df.index, fill_value=False)
            elif isinstance(cache[k], pd.DataFrame):
                # Ensure columns match (some may have been dropped/added)
                cols_to_keep = [c for c in cache[k].columns if c in df.columns]
                cache[k] = cache[k].loc[df.index, cols_to_keep]
                # Add missing columns as False
                for c in df.columns:
                    if c not in cache[k].columns:
                        cache[k][c] = False
                        
        cols_to_process = columns if columns and len(columns) > 0 and columns[0] != 'all' else df.columns.tolist()

        # If data was modified (not just dropped rows), we recalculate the specific columns for the issue
        if issue == "Missing Values" or issue == "Empty Cells" or issue == "Outliers" or issue == "Inconsistent Categories" or issue == "Invalid Data Types":
            # Recompute all masks for the modified columns just to be safe
            partial_cache = MetadataManager.compute_all_masks(df[cols_to_process])
            for k in partial_cache:
                if k == "global_dups": continue
                for c in cols_to_process:
                    cache[k][c] = partial_cache[k][c]
                    
        elif issue in ['Duplicate Rows', 'Exact Duplicates', 'Business Duplicates', 'Near Duplicates']:
            cache["global_dups"] = df.duplicated(keep=False)
            
        return cache
