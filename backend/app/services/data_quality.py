import pandas as pd
import polars as pl
import numpy as np
import re
import gc
from sklearn.ensemble import IsolationForest
from concurrent.futures import ThreadPoolExecutor

class DataQualityService:
    MISSING_VALUES_SET = {
        'nan', 'null', 'none', 'na', 'n/a', '<nan>', '#n/a', '<na>'
    }

    REGEX_EMAIL = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    REGEX_PHONE = r'^\+?[\d\s\-\(\)]{7,15}$'
    REGEX_NUMERIC = r'^-?\d+\.?\d*$'

    @staticmethod
    def analyze_quality(df_pd: pd.DataFrame, masks_cache: dict = None) -> dict:
        total_rows = len(df_pd)
        total_cols = len(df_pd.columns)
        total_cells = total_rows * total_cols
        
        if total_rows == 0:
            return {"error": "Dataset is empty."}
            
        # Smart Analysis Mode limits
        limit_row_output = total_rows > 50000
        extreme_limit = total_rows > 500000
        
        # Sanitize object columns to prevent pyarrow type conversion crashes on mixed types (e.g. str and int)
        for col in df_pd.select_dtypes(include=['object']).columns:
            df_pd[col] = df_pd[col].apply(lambda x: str(x) if pd.notnull(x) else x)
            
        # Convert to Polars for vectorization
        df = pl.from_pandas(df_pd)
        
        def run_missing_empty():
            missing_per_col = {}
            empty_per_col = {}
            total_missing = 0
            total_empty = 0
            
            missing_pct_per_col = {}
            missing_severity = {}

            if masks_cache and "missing_mask" in masks_cache:
                for col in df.columns:
                    col_missing = int(masks_cache["missing_mask"][col].sum()) if col in masks_cache["missing_mask"] else 0
                    col_empty = int(masks_cache["empty_mask"][col].sum()) if col in masks_cache["empty_mask"] else 0
                    
                    missing_per_col[col] = col_missing
                    empty_per_col[col] = col_empty
                    
                    pct = (col_missing / total_rows * 100) if total_rows > 0 else 0.0
                    missing_pct_per_col[col] = round(pct, 2)
                    
                    if pct < 5: sev = "Low"
                    elif pct <= 20: sev = "Medium"
                    elif pct <= 50: sev = "High"
                    else: sev = "Critical"
                    missing_severity[col] = sev
                    
                    total_missing += col_missing
                    total_empty += col_empty
            else:
                for col in df.columns:
                    dtype = df[col].dtype
                    null_count = df[col].null_count()
                    
                    if dtype in [pl.Utf8, pl.Categorical]:
                        col_missing = df.select([
                            (pl.col(col).is_null()) | 
                            (pl.col(col).str.strip_chars().str.to_lowercase().is_in(list(DataQualityService.MISSING_VALUES_SET)))
                        ]).sum().item()
                        col_empty = df.select([
                            (pl.col(col).is_not_null()) & 
                            (pl.col(col).str.strip_chars() == "")
                        ]).sum().item()
                    else:
                        col_missing = null_count
                        col_empty = 0
                        
                    missing_per_col[col] = col_missing
                    empty_per_col[col] = col_empty
                    
                    pct = (col_missing / total_rows * 100) if total_rows > 0 else 0.0
                    missing_pct_per_col[col] = round(pct, 2)
                    
                    if pct < 5: sev = "Low"
                    elif pct <= 20: sev = "Medium"
                    elif pct <= 50: sev = "High"
                    else: sev = "Critical"
                    missing_severity[col] = sev
                    
                    total_missing += col_missing
                    total_empty += col_empty
                
            return total_missing, total_empty, missing_per_col, empty_per_col, missing_pct_per_col, missing_severity

        def run_duplicates():
            if masks_cache and "global_dups" in masks_cache:
                total_duplicates = int(masks_cache["global_dups"].sum())
                row_duplicates_details = []
                col_duplicates_details = []
                columns_containing_duplicates = 0
                dup_count_by_col = {}
                dup_pct_by_col = {}
                total_business_duplicates = 0
                business_keys = []
                total_near_duplicates = 0
                near_duplicates_details = []
                return total_duplicates, row_duplicates_details, col_duplicates_details, columns_containing_duplicates, dup_count_by_col, dup_pct_by_col, total_business_duplicates, business_keys, total_near_duplicates, near_duplicates_details
            
            # Vectorized Exact Duplicates
            dup_mask = df.is_duplicated()
            total_duplicates = dup_mask.sum()
            
            row_duplicates_details = []
            col_duplicates_details = []
            columns_containing_duplicates = 0
            dup_count_by_col = {}
            dup_pct_by_col = {}
            
            # Business Duplicates
            business_keywords = ['id', 'email', 'phone', 'roll', 'customer', 'employee', 'transaction', 'order', 'student']
            business_keys = [c for c in df.columns if any(kw in c.lower() for kw in business_keywords)]
            total_business_duplicates = 0
            business_duplicates_details = []
            
            if business_keys:
                bus_dup_mask = df.select(business_keys).is_duplicated()
                bus_only_mask = bus_dup_mask & ~dup_mask
                total_business_duplicates = bus_only_mask.sum()
                
            # Near Duplicates
            total_near_duplicates = 0
            near_duplicates_details = []
            
            if not extreme_limit and total_rows <= 10000:
                try:
                    from rapidfuzz import fuzz
                    import itertools
                    string_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]
                    for c in string_cols:
                        if c.lower() in [k.lower() for k in business_keys]: continue # Ignore business keys for near dups
                        # Avoid categories like "West", "East", gender, etc.
                        if "region" in c.lower() or "gender" in c.lower() or "city" in c.lower() or "department" in c.lower() or "status" in c.lower() or "category" in c.lower():
                            continue
                        uniques = df.get_column(c).drop_nulls().unique().to_list()
                        if 1 < len(uniques) <= 500: # Limit n^2 comparisons
                            for a, b in itertools.combinations(uniques, 2):
                                if fuzz.ratio(str(a), str(b)) >= 90:
                                    total_near_duplicates += 1
                                    near_duplicates_details.append({"column": c, "val1": a, "val2": b, "similarity": fuzz.ratio(str(a), str(b))})
                except Exception:
                    pass

            if not extreme_limit: 
                if total_duplicates > 0:
                    df_dups = df.with_row_index("row_idx").filter(pl.col("row_idx").is_in(df.with_row_index("row_idx").filter(dup_mask).select("row_idx")))
                    
                    if not df_dups.is_empty():
                        grouped = df_dups.group_by(df.columns).agg(pl.col("row_idx"))
                        grouped = grouped.with_columns(pl.col("row_idx").list.len().alias("dup_len")).sort("dup_len", descending=True).head(100)
                        
                        for row in grouped.iter_rows(named=True):
                            indices = row["row_idx"]
                            indices_1_based = [i + 1 for i in indices]
                            original = indices_1_based[0]
                            dups = indices_1_based[1:]
                            
                            row_duplicates_details.append({
                                "original_row": original,
                                "duplicate_rows": dups[:20],
                                "has_more": len(dups) > 20,
                                "total_duplicates": len(dups)
                            })
                            
                for col in df.columns:
                    val_counts = df.get_column(col).value_counts()
                    dups = val_counts.filter(pl.col("count") > 1)
                    col_total_dups = dups.select(pl.col("count").sum()).item()
                    
                    if col_total_dups is None: col_total_dups = 0
                    
                    dup_count_by_col[col] = col_total_dups
                    dup_pct_by_col[col] = round((col_total_dups / total_rows) * 100, 2)
                    
                    if col_total_dups > 0:
                        columns_containing_duplicates += 1
                        if not limit_row_output:
                            top_dups = dups.sort("count", descending=True).head(10)
                            for row in top_dups.iter_rows(named=True):
                                val = row[col]
                                if val is None: continue
                                
                                indices = df.with_row_index("row_idx").filter(pl.col(col) == val).get_column("row_idx").to_list()
                                indices_1_based = [i + 1 for i in indices]
                                
                                col_duplicates_details.append({
                                    "column": col,
                                    "value": str(val),
                                    "rows": indices_1_based[:20],
                                    "has_more": len(indices_1_based) > 20,
                                    "total_appearances": len(indices_1_based)
                                })
            else:
                # Extreme Limit - No arrays mapped
                for col in df.columns:
                    val_counts = df.get_column(col).value_counts()
                    dups = val_counts.filter(pl.col("count") > 1)
                    col_total_dups = dups.select(pl.col("count").sum()).item()
                    if col_total_dups is None: col_total_dups = 0
                    dup_count_by_col[col] = col_total_dups
                    dup_pct_by_col[col] = round((col_total_dups / total_rows) * 100, 2)
                    if col_total_dups > 0:
                        columns_containing_duplicates += 1

            col_duplicates_details = sorted(col_duplicates_details, key=lambda x: x["total_appearances"], reverse=True)
            return total_duplicates, row_duplicates_details, col_duplicates_details, columns_containing_duplicates, dup_count_by_col, dup_pct_by_col, total_business_duplicates, business_keys, total_near_duplicates, near_duplicates_details

        def run_type_validation():
            type_validation_issues = []
            total_type_mismatches = 0
            string_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]
            
            for col in string_cols:
                valid_df = df.filter(pl.col(col).is_not_null() & (pl.col(col).str.strip_chars() != ""))
                valid_count = len(valid_df)
                if valid_count == 0: continue
                
                num_count = valid_df.filter(pl.col(col).str.contains(DataQualityService.REGEX_NUMERIC)).height
                email_count = valid_df.filter(pl.col(col).str.contains(DataQualityService.REGEX_EMAIL)).height
                phone_count = valid_df.filter(pl.col(col).str.contains(DataQualityService.REGEX_PHONE)).height
                
                if num_count / valid_count > 0.8:
                    mismatch = valid_count - num_count
                    if mismatch > 0:
                        type_validation_issues.append({"column": col, "expected": "Numeric", "mismatch_count": mismatch})
                        total_type_mismatches += mismatch
                elif email_count / valid_count > 0.8:
                    mismatch = valid_count - email_count
                    if mismatch > 0:
                        type_validation_issues.append({"column": col, "expected": "Email", "mismatch_count": mismatch})
                        total_type_mismatches += mismatch
                elif phone_count / valid_count > 0.8:
                    mismatch = valid_count - phone_count
                    if mismatch > 0:
                        type_validation_issues.append({"column": col, "expected": "Phone", "mismatch_count": mismatch})
                        total_type_mismatches += mismatch
            return total_type_mismatches, type_validation_issues

        def run_outliers():
            num_cols = df_pd.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
            outliers_count = 0
            affected_columns = []
            detailed_outliers = []
            
            if not num_cols.empty and total_rows > 10:
                for col in num_cols:
                    col_str = str(col).lower()
                    # Skip ID, name, categorical-like numeric columns
                    if 'id' in col_str or 'name' in col_str or 'phone' in col_str or 'zip' in col_str or 'year' in col_str:
                        continue
                        
                    s = df_pd[col].dropna()
                    if len(s) < 10: continue
                    
                    method = 'IQR'
                    is_large = len(s) > 50000
                    
                    # Normalcy heuristic: mean approx equals median, skewness is low
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
                        outlier_mask = (s < lower) | (s > upper)
                    else:
                        mean = s.mean()
                        std = s.std()
                        if std > 0:
                            outlier_mask = ((s - mean) / std).abs() > 3
                        else:
                            outlier_mask = pd.Series(False, index=s.index)
                            
                    col_outliers_count = int(outlier_mask.sum())
                    if col_outliers_count > 0:
                        outliers_count += col_outliers_count
                        affected_columns.append(col)
                        
                    # Always include detailed stats if eligible for outlier check
                    detailed_outliers.append({
                        "column": col,
                        "total_values": len(s),
                        "outlier_count": col_outliers_count,
                        "outlier_percentage": round((col_outliers_count / len(s)) * 100, 2) if len(s) > 0 else 0,
                        "method": method,
                        "bounds": {"lower": float(lower) if method == 'IQR' else float(mean - 3*std) if std>0 else None, 
                                   "upper": float(upper) if method == 'IQR' else float(mean + 3*std) if std>0 else None}
                    })
                        
            return outliers_count, affected_columns, detailed_outliers

        def run_string_anomalies():
            constant_cols = []
            high_cardinality_cols = []
            extra_spaces_cols = []
            special_chars_cols = []
            
            for col in df.columns:
                unique_count = df.get_column(col).n_unique()
                if unique_count == 1:
                    constant_cols.append(col)
                
                if df[col].dtype in [pl.Utf8, pl.Categorical] and total_rows > 10:
                    if unique_count / total_rows > 0.9:
                        high_cardinality_cols.append(col)
                        
                    has_spaces = df.select(pl.col(col).str.contains(r'^\s+|\s+$')).sum().item()
                    if has_spaces and has_spaces > 0:
                        extra_spaces_cols.append(col)
                        
                    has_special = df.select(pl.col(col).str.contains(r'[^\w\s\.\,\-\@\_]')).sum().item()
                    if has_special and has_special > 0:
                        special_chars_cols.append(col)
                        
            return constant_cols, high_cardinality_cols, extra_spaces_cols, special_chars_cols

        # Execute Parallel Threading
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_missing = executor.submit(run_missing_empty)
            future_dups = executor.submit(run_duplicates)
            future_types = executor.submit(run_type_validation)
            future_outliers = executor.submit(run_outliers)
            future_anomalies = executor.submit(run_string_anomalies)
            
            total_missing, total_empty, missing_per_col, empty_per_col, missing_pct_per_col, missing_severity = future_missing.result()
            total_duplicates, row_duplicates_details, col_duplicates_details, columns_containing_duplicates, dup_count_by_col, dup_pct_by_col, total_business_duplicates, business_keys, total_near_duplicates, near_duplicates_details = future_dups.result()
            total_type_mismatches, type_validation_issues = future_types.result()
            outliers_count, affected_columns, detailed_outliers = future_outliers.result()
            constant_cols, high_cardinality_cols, extra_spaces_cols, special_chars_cols = future_anomalies.result()

        # Advanced Anomalies
        inconsistent_categories_cols = []
        date_format_problems_cols = []
        duplicate_columns = []
        high_null_cols = []
        
        for col in df_pd.columns:
            missing = missing_per_col.get(col, 0)
            empty = empty_per_col.get(col, 0)
            if total_rows > 0 and (missing + empty) / total_rows > 0.70:
                high_null_cols.append(col)
                
        if not df_pd.empty:
            for i in range(len(df_pd.columns)):
                col1 = df_pd.columns[i]
                for j in range(i + 1, len(df_pd.columns)):
                    col2 = df_pd.columns[j]
                    if df_pd[col1].dtype == df_pd[col2].dtype:
                        if df_pd[col1].isnull().sum() == df_pd[col2].isnull().sum():
                            if df_pd[col1].equals(df_pd[col2]):
                                duplicate_columns.append(col2)
        duplicate_columns = list(set(duplicate_columns))
        
        string_cols = df_pd.select_dtypes(include=['object', 'string']).columns
        for col in string_cols:
            valid_pd = df_pd[col].dropna()
            valid_pd = valid_pd[valid_pd.astype(str).str.strip() != ""]
            if len(valid_pd) == 0: continue
            
            original_uniques = valid_pd.nunique()
            if 0 < original_uniques < 1000:
                lower_uniques = valid_pd.astype(str).str.lower().nunique()
                if lower_uniques < original_uniques:
                    inconsistent_categories_cols.append(col)
                    
            sample_pd = valid_pd.head(1000).astype(str)
            has_slash = sample_pd.str.contains(r'/').any()
            has_dash = sample_pd.str.contains(r'-').any()
            has_alpha = sample_pd.str.contains(r'[a-zA-Z]').any()
            
            is_likely_date = sample_pd.str.match(r'^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}').sum() / len(sample_pd) > 0.5
            if not is_likely_date:
                is_likely_date = sample_pd.str.match(r'^[a-zA-Z]{3}[-\s]\d{1,2}[-\s]\d{2,4}').sum() / len(sample_pd) > 0.5
                
            if is_likely_date:
                if (has_slash and has_dash) or (has_alpha and has_slash) or (has_alpha and has_dash):
                    date_format_problems_cols.append(col)

        # Clean memory immediately
        del df
        gc.collect()

        # Score calculations
        completeness = max(0, 100.0 - ((total_missing + total_empty) / total_cells * 100) if total_cells > 0 else 100.0)
        consistency = max(0, 100.0 - (total_duplicates / total_rows * 100) if total_rows > 0 else 100.0)
        uniqueness = max(0, 100.0 - (total_duplicates / total_rows * 100) if total_rows > 0 else 100.0)
        
        num_cols = df_pd.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
        outlier_pct = (outliers_count / (total_rows * len(num_cols)) * 100) if len(num_cols) > 0 and total_rows > 0 else 0.0
        mismatch_pct = (total_type_mismatches / total_cells * 100) if total_cells > 0 else 0.0
        
        missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0.0
        empty_pct = (total_empty / total_cells * 100) if total_cells > 0 else 0.0
        duplicate_pct = (total_duplicates / total_rows * 100) if total_rows > 0 else 0.0
        
        validity = max(0, 100.0 - (outlier_pct + mismatch_pct))
        accuracy = (completeness + consistency + validity + uniqueness) / 4
        
        top_10_missing = dict(sorted(missing_per_col.items(), key=lambda item: item[1], reverse=True)[:10])

        # Deep Actionable Analysis Additions
        # 1. High Empty Columns (>30%)
        high_empty_cols = [col for col, pct in missing_pct_per_col.items() if pct > 30]

        # 2. Row Quality Analysis (>50% empty cells per row)
        # We can calculate the missing/empty percentage per row
        row_missing_mask = df_pd.isna() | df_pd.isin(["", " "])
        row_missing_counts = row_missing_mask.sum(axis=1)
        poor_quality_rows_count = int((row_missing_counts > (total_cols / 2)).sum())

        # 3. Missing Data Heatmap
        # Create a boolean mask of the dataset (1 for missing/empty, 0 for present). Downsample to max 100 rows.
        sample_size = min(100, total_rows)
        if sample_size > 0:
            df_sample = row_missing_mask.sample(n=sample_size, random_state=42) if total_rows > 100 else row_missing_mask
            heatmap_data = []
            for idx, row in df_sample.iterrows():
                row_data = {"_row_id": int(idx)}
                for col in df_pd.columns:
                    row_data[str(col)] = 1 if row[col] else 0
                heatmap_data.append(row_data)
        else:
            heatmap_data = []

        # 4. Unique Value Analysis & 5. Column Importance
        unique_counts_by_col = {}
        column_importance = {}
        for col in df_pd.columns:
            # We already have uniqueness counts in run_string_anomalies, but let's quickly compute it for all
            uniques = int(df_pd[col].nunique(dropna=True))
            unique_counts_by_col[col] = uniques
            
            # Column Importance Score: Start at 100, subtract missing_pct, subtract if constant
            missing_pct_val = missing_pct_per_col.get(col, 0)
            score = 100 - missing_pct_val
            if uniques <= 1:
                score -= 100  # Constant columns are useless
            elif df_pd[col].dtype == 'object' and uniques > 0.9 * total_rows:
                score -= 50   # High cardinality IDs are less useful for ML/Analytics
            
            if score >= 80:
                imp = "High"
            elif score >= 50:
                imp = "Medium"
            else:
                imp = "Low"
            column_importance[col] = imp

        return {
            "metrics": {
                "total_rows": total_rows,
                "total_cols": total_cols,
                "total_cells": total_cells,
                "total_missing_values": total_missing,
                "total_empty_cells": total_empty,
                "total_exact_duplicates": total_duplicates,
                "total_outliers": outliers_count,
                "total_type_mismatches": total_type_mismatches,
                "total_constant_cols": len(constant_cols),
                "total_high_cardinality_cols": len(high_cardinality_cols),
                "total_extra_spaces_cols": len(extra_spaces_cols),
                "total_special_chars_cols": len(special_chars_cols),
                "total_duplicate_columns": len(duplicate_columns),
                "total_business_duplicates": total_business_duplicates,
                "total_near_duplicates": total_near_duplicates,
                "total_inconsistent_categories": len(inconsistent_categories_cols),
                "total_date_format_problems": len(date_format_problems_cols),
                "total_high_null_cols": len(high_null_cols)
            },
            "scores": {
                "completeness": round(completeness, 2),
                "consistency": round(consistency, 2),
                "validity": round(validity, 2),
                "uniqueness": round(uniqueness, 2),
                "accuracy": round(accuracy, 2),
                "overall_cleanliness": round(accuracy, 2),
                "missing_pct": round(missing_pct, 2),
                "empty_pct": round(empty_pct, 2),
                "duplicate_pct": round(duplicate_pct, 2),
                "outlier_pct": round(outlier_pct, 2)
            },
            "distributions": {
                "missing_per_column": top_10_missing,
                "all_missing_per_column": missing_per_col,
                "missing_pct_per_column": missing_pct_per_col,
                "missing_severity": missing_severity,
                "empty_per_column": empty_per_col,
                "duplicate_count_by_col": dup_count_by_col,
                "duplicate_pct_by_col": dup_pct_by_col,
                "unique_counts_by_col": unique_counts_by_col,
                "column_importance": column_importance
            },
            "anomalies": {
                "row_duplicates_details": row_duplicates_details,
                "col_duplicates_details": col_duplicates_details,
                "columns_containing_duplicates": columns_containing_duplicates,
                "type_validation_issues": type_validation_issues,
                "outlier_columns": affected_columns,
                "constant_cols": constant_cols,
                "high_cardinality_cols": high_cardinality_cols,
                "extra_spaces_cols": extra_spaces_cols,
                "special_chars_cols": special_chars_cols,
                "duplicate_columns": duplicate_columns,
                "business_keys": business_keys,
                "near_duplicates_details": near_duplicates_details,
                "inconsistent_categories_cols": inconsistent_categories_cols,
                "date_format_problems_cols": date_format_problems_cols,
                "high_null_cols": high_null_cols,
                "detailed_outliers": detailed_outliers,
                "high_empty_cols": high_empty_cols,
                "poor_quality_rows_count": poor_quality_rows_count,
                "missing_data_heatmap": heatmap_data
            }
        }
