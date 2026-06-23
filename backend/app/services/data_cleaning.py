import pandas as pd
import numpy as np

class DataCleaningService:
    @staticmethod
    def apply_targeted_cleaning(df: pd.DataFrame, issue: str, columns: list, method: str, custom_value: str = None) -> pd.DataFrame:
        cols_to_process = columns if columns and len(columns) > 0 and columns[0] != 'all' else df.columns.tolist()
        
        # Heavy operations optimized with Polars
        if issue in ['Missing Values', 'Empty Cells', 'Outliers', 'Duplicate Rows', 'Exact Duplicates', 'Business Duplicates', 'Near Duplicates', 'Extra Spaces', 'Special Characters']:
            import polars as pl
            from app.services.data_quality import DataQualityService
            
            # Sanitize mixed type object columns before polars conversion
            df_safe = df.copy()
            for col in df_safe.select_dtypes(include=['object']).columns:
                df_safe[col] = df_safe[col].apply(lambda x: str(x) if pd.notnull(x) else x)
                
            pldf = pl.from_pandas(df_safe, include_index=True)
            index_col = pldf.columns[0] # Usually 'index'
            
            if issue == 'Missing Values':
                missing_set = DataQualityService.MISSING_VALUES_SET
                
                # First, standardize missing values to null
                for col in cols_to_process:
                    if pldf[col].dtype in [pl.Utf8, pl.Categorical]:
                        pldf = pldf.with_columns(
                            pl.when(pl.col(col).str.strip_chars().str.to_lowercase().is_in(list(missing_set)))
                            .then(None)
                            .otherwise(pl.col(col))
                            .alias(col)
                        )
                
                if method == 'Drop Rows':
                    pldf = pldf.drop_nulls(subset=cols_to_process)
                elif method == 'Drop Column':
                    pldf = pldf.drop(cols_to_process)
                elif method == 'Replace with Unknown':
                    for col in cols_to_process:
                        pldf = pldf.with_columns(pl.col(col).fill_null("Unknown"))
                elif method == 'Mean Imputation':
                    for col in cols_to_process:
                        if pldf[col].dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                            pldf = pldf.with_columns(pl.col(col).fill_null(pl.col(col).mean()))
                elif method == 'Median Imputation':
                    for col in cols_to_process:
                        if pldf[col].dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                            pldf = pldf.with_columns(pl.col(col).fill_null(pl.col(col).median()))
                elif method in ['Mode Imputation', 'Forward Fill', 'Backward Fill', 'Interpolate']:
                    # Fallback to pandas for complex imputations
                    cleaned_df = pldf.to_pandas().set_index(index_col)
                    cleaned_df.index.name = df.index.name
                    for col in cols_to_process:
                        if method == 'Mode Imputation':
                            if not cleaned_df[col].mode().empty:
                                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])
                        elif method == 'Forward Fill':
                            cleaned_df[col] = cleaned_df[col].ffill()
                        elif method == 'Backward Fill':
                            cleaned_df[col] = cleaned_df[col].bfill()
                        elif method == 'Interpolate':
                            if pd.api.types.is_numeric_dtype(cleaned_df[col]) or pd.api.types.is_datetime64_any_dtype(cleaned_df[col]):
                                cleaned_df[col] = cleaned_df[col].interpolate()
                    return cleaned_df
            
            elif issue == 'Empty Cells':
                if method == 'Remove Rows':
                    # Drop row if ANY column in cols_to_process is empty string
                    exprs = [(pl.col(c).is_not_null()) & (pl.col(c).cast(pl.Utf8).str.strip_chars() == "") for c in cols_to_process if pldf[c].dtype in [pl.Utf8, pl.Categorical]]
                    if exprs:
                        mask = pl.any_horizontal(exprs)
                        pldf = pldf.filter(~mask)
                else:
                    for col in cols_to_process:
                        if pldf[col].dtype in [pl.Utf8, pl.Categorical]:
                            is_empty = (pl.col(col).is_not_null()) & (pl.col(col).str.strip_chars() == "")
                            if method == 'Replace with Default Value':
                                pldf = pldf.with_columns(pl.when(is_empty).then(pl.lit("Unknown")).otherwise(pl.col(col)).alias(col))
                            elif method == 'Replace with Custom User Value':
                                pldf = pldf.with_columns(pl.when(is_empty).then(pl.lit(custom_value or "Unknown")).otherwise(pl.col(col)).alias(col))
                            elif method == 'Replace with Mode':
                                # Fallback to pandas for mode calculation
                                cleaned_df = pldf.to_pandas().set_index(index_col)
                                valid_data = cleaned_df[col][~cleaned_df[col].astype(str).str.match(r'^\s*$', na=False)]
                                if not valid_data.mode().empty:
                                    cleaned_df[col] = cleaned_df[col].replace(r'^\s*$', valid_data.mode()[0], regex=True)
                                return cleaned_df
                                
            elif issue == 'Outliers':
                for col in cols_to_process:
                    if pldf[col].dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                        s = pldf[col].drop_nulls()
                        if len(s) < 10: continue
                        
                        q1 = s.quantile(0.25)
                        q3 = s.quantile(0.75)
                        iqr = q3 - q1
                        lower = q1 - 1.5 * iqr
                        upper = q3 + 1.5 * iqr
                        
                        is_outlier = (pl.col(col) < lower) | (pl.col(col) > upper)
                        
                        if method == 'Remove Outliers':
                            pldf = pldf.filter(~is_outlier | pl.col(col).is_null())
                        elif method == 'Cap to Upper Bound':
                            pldf = pldf.with_columns(pl.when(pl.col(col) > upper).then(pl.lit(upper)).otherwise(pl.col(col)).alias(col))
                        elif method == 'Replace with Median':
                            med = s.median()
                            pldf = pldf.with_columns(pl.when(is_outlier).then(pl.lit(med)).otherwise(pl.col(col)).alias(col))
                        elif method == 'Replace with Mean':
                            mean_val = s.mean()
                            pldf = pldf.with_columns(pl.when(is_outlier).then(pl.lit(mean_val)).otherwise(pl.col(col)).alias(col))

            elif issue in ['Duplicate Rows', 'Exact Duplicates', 'Business Duplicates', 'Near Duplicates']:
                subset = cols_to_process if cols_to_process and cols_to_process[0] != 'all' else None
                if method == 'Remove Exact Duplicates' or method == 'Keep First Occurrence':
                    pldf = pldf.unique(subset=subset, keep='first')
                elif method == 'Keep Latest Occurrence':
                    pldf = pldf.unique(subset=subset, keep='last')
                elif method == 'Merge Records':
                    # Fallback to pandas for complex merge/ffill
                    cleaned_df = pldf.to_pandas().set_index(index_col)
                    cleaned_df.index.name = df.index.name
                    if subset:
                        cleaned_df = cleaned_df.groupby(subset, as_index=False).apply(lambda x: x.bfill().ffill().iloc[0]).reset_index(drop=True)
                    else:
                        cleaned_df = cleaned_df.drop_duplicates(keep='first')
                    return cleaned_df
                    
            elif issue == 'Extra Spaces' and method == 'Trim Spaces':
                for col in cols_to_process:
                    if pldf[col].dtype in [pl.Utf8, pl.Categorical]:
                        pldf = pldf.with_columns(pl.col(col).str.strip_chars().alias(col))
                        
            elif issue == 'Special Characters' and method == 'Remove Special Characters':
                for col in cols_to_process:
                    if pldf[col].dtype in [pl.Utf8, pl.Categorical]:
                        pldf = pldf.with_columns(pl.col(col).str.replace_all(r'[^\w\s\.\,\-\@\_]', '').alias(col))
            
            # Convert back to pandas
            res = pldf.to_pandas().set_index(index_col)
            res.index.name = df.index.name
            return res

        # Fallback to pandas for other methods
        cleaned_df = df.copy()
        
        if issue == 'Constant Columns' or issue == 'High Cardinality':
            if method == 'Drop Column':
                cleaned_df = cleaned_df.drop(columns=cols_to_process, errors='ignore')
                
        elif issue == 'Invalid Data Types':
            if method == 'Convert to Numeric':
                for col in cols_to_process:
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
            elif method == 'Convert to String':
                for col in cols_to_process:
                    cleaned_df[col] = cleaned_df[col].astype(str)
                    
        elif issue == 'Duplicate Columns' or issue == 'High Null Percentage Columns':
            if method == 'Drop Duplicate Columns' or method == 'Drop Columns':
                cleaned_df = cleaned_df.drop(columns=cols_to_process, errors='ignore')
                
        elif issue == 'Inconsistent Categories':
            if method == 'Standardize Format':
                for col in cols_to_process:
                    if cleaned_df[col].dtype == 'object' or cleaned_df[col].dtype == 'string':
                        cleaned_df[col] = cleaned_df[col].astype(str).str.title()
                        
        elif issue == 'Date Format Problems':
            if method == 'Convert to Single Format':
                for col in cols_to_process:
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], format='mixed', errors='coerce').dt.strftime('%Y-%m-%d')
                    
        elif issue == 'Manual Removal':
            if method == 'Drop Column':
                cleaned_df = cleaned_df.drop(columns=cols_to_process, errors='ignore')
            elif method == 'Drop Row':
                try:
                    if custom_value:
                        idx_to_drop = [int(x.strip()) for x in str(custom_value).split(',')]
                        valid_idx = [i for i in idx_to_drop if i in cleaned_df.index]
                        if valid_idx:
                            cleaned_df = cleaned_df.drop(index=valid_idx)
                except (ValueError, TypeError):
                    pass
                        
        return cleaned_df
