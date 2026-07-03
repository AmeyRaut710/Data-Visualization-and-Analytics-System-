import polars as pl
import gc
from concurrent.futures import ThreadPoolExecutor

class DataQualityService:
    MISSING_VALUES_SET = {'nan', 'null', 'none', 'na', 'n/a', '<nan>', '#n/a', '<na>', '?'}
    REGEX_EMAIL = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    REGEX_PHONE = r'^\+?[\d\s\-\(\)]{7,15}$'
    REGEX_NUMERIC = r'^-?\d+\.?\d*$'

    @staticmethod
    def analyze_quality(df: pl.DataFrame, masks_cache: dict = None) -> dict:
        total_rows = df.height
        total_cols = df.width
        total_cells = total_rows * total_cols
        
        if total_rows == 0:
            return {"error": "Dataset is empty."}
            
        limit_row_output = total_rows > 50000
        extreme_limit = total_rows > 500000
        
        def run_missing_empty():
            missing_per_col = {}
            empty_per_col = {}
            total_missing = 0
            total_empty = 0
            missing_pct_per_col = {}
            missing_severity = {}

            if masks_cache and "missing_indices" in masks_cache:
                for col in df.columns:
                    col_missing = len(masks_cache["missing_indices"].get(col, []))
                    col_empty = len(masks_cache.get("empty_indices", {}).get(col, []))
                    
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
                # Fallback if no cache
                for col in df.columns:
                    dtype = df.schema[col]
                    if dtype in [pl.Utf8, pl.Categorical]:
                        col_missing = df.select([(pl.col(col).is_null()) | (pl.col(col).str.strip_chars().str.to_lowercase().is_in(list(DataQualityService.MISSING_VALUES_SET)))]).sum().item()
                        col_empty = df.select([(pl.col(col).is_not_null()) & (pl.col(col).str.strip_chars() == "")]).sum().item()
                    else:
                        if dtype in [pl.Float32, pl.Float64]:
                            col_missing = df.select([(pl.col(col).is_null()) | (pl.col(col).is_nan())]).sum().item()
                        else:
                            col_missing = df.get_column(col).null_count()
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
            total_business_duplicates = 0
            total_near_duplicates = 0
            business_keys = []
            near_duplicates_details = []
            row_duplicates_details = []
            col_duplicates_details = []
            columns_containing_duplicates = 0
            dup_count_by_col = {}
            dup_pct_by_col = {}

            if masks_cache and "dup_groups" in masks_cache:
                total_duplicates = len(masks_cache.get("global_dups_idx", []))
                if not extreme_limit:
                    for group in masks_cache["dup_groups"][:100]:
                        original_row = group[0]
                        duplicate_rows = group[1:]
                        total_group_dups = len(duplicate_rows)
                        row_duplicates_details.append({
                            "original_row": original_row,
                            "duplicate_rows": duplicate_rows[:5],
                            "has_more": total_group_dups > 5,
                            "total_duplicates": total_group_dups
                        })
            elif masks_cache and "global_dups_idx" in masks_cache:
                total_duplicates = len(masks_cache["global_dups_idx"])
            else:
                total_duplicates = df.is_duplicated().sum()
                
            # For brevity in high-performance mode, we skip detailed row mapping for extremes
            if not extreme_limit:
                # Column duplicates (computed in parallel)
                dup_counts = df.select(pl.all().is_duplicated().sum()).to_dicts()[0]
                for col in df.columns:
                    col_total_dups = dup_counts[col]
                    dup_count_by_col[col] = col_total_dups
                    dup_pct_by_col[col] = round((col_total_dups / total_rows) * 100, 2) if total_rows > 0 else 0
                    if col_total_dups > 0:
                        columns_containing_duplicates += 1
                        
            return total_duplicates, row_duplicates_details, col_duplicates_details, columns_containing_duplicates, dup_count_by_col, dup_pct_by_col, total_business_duplicates, business_keys, total_near_duplicates, near_duplicates_details

        def run_type_validation():
            type_validation_issues = []
            total_type_mismatches = 0
            
            if masks_cache and "invalid_type_indices" in masks_cache:
                for col, indices in masks_cache["invalid_type_indices"].items():
                    mismatch = len(indices)
                    if mismatch > 0:
                        type_validation_issues.append({"column": col, "expected": "Numeric/Email/Phone", "mismatch_count": mismatch})
                        total_type_mismatches += mismatch
            return total_type_mismatches, type_validation_issues

        def run_outliers():
            outliers_count = 0
            affected_columns = []
            detailed_outliers = []
            
            if masks_cache and "outlier_indices" in masks_cache:
                stats = masks_cache.get("stats", {})
                for col, indices in masks_cache["outlier_indices"].items():
                    cnt = len(indices)
                    if cnt > 0:
                        outliers_count += cnt
                        affected_columns.append(col)
                        
                        col_stats = stats.get(col, {})
                        method = col_stats.get('outlier_method', 'Unknown')
                        lower = col_stats.get('lower_bound', None)
                        upper = col_stats.get('upper_bound', None)
                        
                        outlier_rows = []
                        if not extreme_limit:
                            preview_indices = indices[:5]
                            for idx in preview_indices:
                                try:
                                    val = df[col][idx]
                                    outlier_rows.append({"row": idx, "value": val})
                                except Exception:
                                    pass
                                
                        detailed_outliers.append({
                            "column": col,
                            "outlier_count": cnt,
                            "outlier_percentage": round((cnt / total_rows) * 100, 2) if total_rows > 0 else 0,
                            "method": method,
                            "lower_bound": lower,
                            "upper_bound": upper,
                            "outlier_rows": outlier_rows
                        })
            return outliers_count, affected_columns, detailed_outliers

        def run_string_anomalies():
            constant_cols = []
            high_cardinality_cols = []
            extra_spaces_cols = []
            special_chars_cols = []
            
            # Compute uniques for all columns in parallel
            uniques = df.select(pl.all().n_unique()).to_dicts()[0]
            
            for col in df.columns:
                unique_count = uniques[col]
                if unique_count == 1:
                    constant_cols.append(col)
                
                if df.schema[col] in [pl.Utf8, pl.Categorical] and total_rows > 10:
                    if unique_count / total_rows > 0.9:
                        high_cardinality_cols.append(col)
                        
            return constant_cols, high_cardinality_cols, extra_spaces_cols, special_chars_cols

        total_missing, total_empty, missing_per_col, empty_per_col, missing_pct_per_col, missing_severity = run_missing_empty()
        total_duplicates, row_duplicates_details, col_duplicates_details, columns_containing_duplicates, dup_count_by_col, dup_pct_by_col, total_business_duplicates, business_keys, total_near_duplicates, near_duplicates_details = run_duplicates()
        total_type_mismatches, type_validation_issues = run_type_validation()
        outliers_count, affected_columns, detailed_outliers = run_outliers()
        constant_cols, high_cardinality_cols, extra_spaces_cols, special_chars_cols = run_string_anomalies()
        
        inconsistent_categories_cols = []
        if masks_cache and "inconsistent_cat_indices" in masks_cache:
            inconsistent_categories_cols = list(masks_cache["inconsistent_cat_indices"].keys())
            
        date_format_problems_cols = []
        duplicate_columns = []
        high_null_cols = [col for col, pct in missing_pct_per_col.items() if pct > 70.0]
        high_empty_cols = [col for col, pct in missing_pct_per_col.items() if pct > 30.0]

        # Score calculations
        completeness = max(0, 100.0 - ((total_missing + total_empty) / total_cells * 100) if total_cells > 0 else 100.0)
        consistency = max(0, 100.0 - (total_duplicates / total_rows * 100) if total_rows > 0 else 100.0)
        uniqueness = max(0, 100.0 - (total_duplicates / total_rows * 100) if total_rows > 0 else 100.0)
        
        num_cols = [c for c, d in zip(df.columns, df.dtypes) if d in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]]
        outlier_pct = (outliers_count / (total_rows * len(num_cols)) * 100) if len(num_cols) > 0 and total_rows > 0 else 0.0
        mismatch_pct = (total_type_mismatches / total_cells * 100) if total_cells > 0 else 0.0
        
        missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0.0
        empty_pct = (total_empty / total_cells * 100) if total_cells > 0 else 0.0
        duplicate_pct = (total_duplicates / total_rows * 100) if total_rows > 0 else 0.0
        
        validity = max(0, 100.0 - (outlier_pct + mismatch_pct))
        accuracy = (completeness + consistency + validity + uniqueness) / 4
        
        top_10_missing = dict(sorted(missing_per_col.items(), key=lambda item: item[1], reverse=True)[:10])

        column_importance = {}
        for col in df.columns:
            score = 100 - missing_pct_per_col.get(col, 0)
            if col in constant_cols: score -= 100
            elif col in high_cardinality_cols: score -= 50
            
            if score >= 80: imp = "High"
            elif score >= 50: imp = "Medium"
            else: imp = "Low"
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
                "poor_quality_rows_count": 0,
                "missing_data_heatmap": []
            }
        }
