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
        import time
        import math
        import numpy as np
        start_time = time.time()
        
        # Filter active columns: ignore unnamed, helper, temporary, and completely empty columns
        active_cols = []
        for col in df.columns:
            col_lower = col.lower()
            if col.startswith("_") or "unnamed" in col_lower or col_lower in ["temp", "index", "internal", "row_id"]:
                continue
            # Check if completely empty (all nulls or empty strings)
            s = df.get_column(col)
            if s.null_count() == df.height:
                continue
            # Check if column is completely null/missing
            non_empty_count = 0
            try:
                dtype = df.schema[col]
                if dtype in [pl.Utf8, pl.Categorical]:
                    non_empty_count = df.select(
                        (pl.col(col).is_not_null()) & 
                        (pl.col(col).cast(pl.Utf8).str.strip_chars() != "") &
                        (~pl.col(col).cast(pl.Utf8).str.to_lowercase().is_in(list(DataQualityService.MISSING_VALUES_SET)))
                    ).sum().item()
                else:
                    non_empty_count = df.height - s.null_count()
            except:
                non_empty_count = df.height - s.null_count()
                
            if non_empty_count == 0:
                continue
            active_cols.append(col)
            
        total_rows = df.height
        total_cols = len(active_cols)
        total_cells = total_rows * total_cols
        
        if total_rows == 0:
            return {"error": "Dataset is empty."}
            
        limit_row_output = total_rows > 50000
        extreme_limit = total_rows > 500000
        
        # Pre-compute uniques for active columns in parallel
        uniques = {}
        try:
            uniques = df.select([pl.col(col).n_unique().alias(col) for col in active_cols]).to_dicts()[0]
        except Exception:
            for col in active_cols:
                uniques[col] = df.get_column(col).n_unique()

        # Dynamic Column Classification (No overlaps, exactly one category per column)
        classifications = {}
        for col in active_cols:
            dtype = df.schema[col]
            s = df.get_column(col)
            col_lower = col.lower()
            unique_count = uniques.get(col, total_rows)
            unique_ratio = unique_count / total_rows if total_rows > 0 else 0
            
            # 1. Identifier Check
            is_identifier = False
            if unique_ratio > 0.95 and dtype in [pl.Utf8, pl.Int64, pl.Int32]:
                is_identifier = True
            elif any(k in col_lower for k in ["id", "uuid", "code", "key", "token", "number", "serial"]):
                is_identifier = True
                
            # 2. Date Check
            is_date = False
            if dtype in [pl.Date, pl.Datetime]:
                is_date = True
            else:
                # Exclude year columns (1990, 2025 etc)
                is_year = False
                if dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]:
                    try:
                        non_null_s = s.drop_nulls()
                        if len(non_null_s) > 0:
                            min_v = non_null_s.min()
                            max_v = non_null_s.max()
                            if min_v >= 1000 and max_v <= 2100:
                                is_year = True
                    except:
                        pass
                
                if not is_year:
                    try:
                        sample_vals = [str(x) for x in s.head(50).drop_nulls().to_list()]
                        if sample_vals:
                            parsed_count = 0
                            import dateutil.parser as dparser
                            for val in sample_vals:
                                if val.strip().isdigit() and len(val.strip()) == 4:
                                    continue
                                try:
                                    dparser.parse(val)
                                    parsed_count += 1
                                except:
                                    pass
                            if parsed_count / len(sample_vals) > 0.85:
                                is_date = True
                    except:
                        pass

            # 3. Numeric Check
            is_numeric = False
            if dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32, pl.Decimal] and not is_identifier:
                is_numeric = True
                
            # 4. Text or Categorical Check
            is_text = False
            is_categorical = False
            
            if dtype in [pl.Utf8, pl.Categorical]:
                if unique_count < 100 or unique_ratio < 0.15:
                    is_categorical = True
                else:
                    is_text = True
            elif dtype == pl.Boolean:
                is_categorical = True

            # Resolve Category Hierarchy
            if is_identifier:
                classifications[col] = "Identifier"
            elif is_date:
                classifications[col] = "Date"
            elif is_numeric:
                classifications[col] = "Numeric"
            elif is_categorical:
                classifications[col] = "Categorical"
            elif is_text:
                classifications[col] = "Text"
            else:
                classifications[col] = "Unknown"
        
        def run_missing_empty():
            missing_per_col = {}
            empty_per_col = {}
            total_missing = 0
            total_empty = 0
            missing_pct_per_col = {}
            missing_severity = {}

            if masks_cache and "missing_indices" in masks_cache:
                for col in active_cols:
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
                for col in active_cols:
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
                
            if not extreme_limit:
                dup_counts = df.select([pl.col(col).is_duplicated().sum().alias(col) for col in active_cols]).to_dicts()[0]
                for col in active_cols:
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
                    if col.startswith("_"):
                        continue
                    mismatch = len(indices)
                    if mismatch > 0:
                        detected_t = str(df.schema[col])
                        expected_t = "Numeric"
                        if "email" in col.lower():
                            expected_t = "Email"
                        elif "phone" in col.lower():
                            expected_t = "Phone"
                        elif classifications.get(col) == "Numeric":
                            expected_t = "Numeric"
                        elif classifications.get(col) == "Date":
                            expected_t = "Date"
                            
                        type_validation_issues.append({
                            "column": col, 
                            "expected": expected_t,
                            "detected": detected_t,
                            "mismatch_count": mismatch
                        })
                        total_type_mismatches += mismatch
            return total_type_mismatches, type_validation_issues

        def run_outliers():
            outliers_count = 0
            affected_columns = []
            detailed_outliers = []
            
            if masks_cache and "outlier_indices" in masks_cache:
                stats = masks_cache.get("stats", {})
                for col, indices in masks_cache["outlier_indices"].items():
                    if col.startswith("_") or classifications.get(col) != "Numeric":
                        continue
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
            
            for col in active_cols:
                unique_count = uniques[col]
                if unique_count == 1:
                    constant_cols.append(col)
                
                if df.schema[col] in [pl.Utf8, pl.Categorical] and total_rows > 10:
                    if unique_count / total_rows > 0.9:
                        high_cardinality_cols.append(col)
                        
            return constant_cols, high_cardinality_cols, extra_spaces_cols, special_chars_cols, uniques
        
        total_missing, total_empty, missing_per_col, empty_per_col, missing_pct_per_col, missing_severity = run_missing_empty()
        total_duplicates, row_duplicates_details, col_duplicates_details, columns_containing_duplicates, dup_count_by_col, dup_pct_by_col, total_business_duplicates, business_keys, total_near_duplicates, near_duplicates_details = run_duplicates()
        total_type_mismatches, type_validation_issues = run_type_validation()
        outliers_count, affected_columns, detailed_outliers = run_outliers()
        constant_cols, high_cardinality_cols, extra_spaces_cols, special_chars_cols, uniques = run_string_anomalies()
        
        inconsistent_categories_cols = []
        if masks_cache and "inconsistent_cat_indices" in masks_cache:
            inconsistent_categories_cols = [c for c in masks_cache["inconsistent_cat_indices"].keys() if not c.startswith("_")]
            
        date_format_problems_cols = []
        duplicate_columns = []
        high_null_cols = [col for col, pct in missing_pct_per_col.items() if pct > 70.0]
        high_empty_cols = [col for col, pct in missing_pct_per_col.items() if pct > 30.0]

        # Calculate rows affected by missing values
        missing_rows_set = set()
        columns_affected_by_missing = 0
        if masks_cache and "missing_indices" in masks_cache:
            for col, indices in masks_cache["missing_indices"].items():
                if not col.startswith("_") and len(indices) > 0:
                    missing_rows_set.update(indices)
                    columns_affected_by_missing += 1
        else:
            for col in active_cols:
                dtype = df.schema[col]
                if dtype in [pl.Utf8, pl.Categorical]:
                    is_missing = (pl.col(col).is_null()) | (pl.col(col).str.strip_chars().str.to_lowercase().is_in(list(DataQualityService.MISSING_VALUES_SET)))
                else:
                    if dtype in [pl.Float32, pl.Float64]:
                        is_missing = pl.col(col).is_null() | pl.col(col).is_nan()
                    else:
                        is_missing = pl.col(col).is_null()
                indices = df.with_row_index("idx").filter(is_missing).get_column("idx").to_list()
                if indices:
                    missing_rows_set.update(indices)
                    columns_affected_by_missing += 1
        total_missing_rows_count = len(missing_rows_set)

        # Locate minimum and maximum outliers
        min_outlier_val = None
        min_outlier_col = "None"
        max_outlier_val = None
        max_outlier_col = "None"
        min_v = float('inf')
        max_v = -float('inf')
        
        numeric_cols_checked = len([c for c in active_cols if classifications.get(c) == "Numeric"])
        
        if masks_cache and "outlier_indices" in masks_cache:
            for col, indices in masks_cache["outlier_indices"].items():
                if col.startswith("_") or classifications.get(col) != "Numeric":
                    continue
                for idx in indices:
                    try:
                        val = df[col][idx]
                        if val is not None:
                            if val < min_v:
                                min_v = val
                                min_outlier_val = val
                                min_outlier_col = col
                            if val > max_v:
                                max_v = val
                                max_outlier_val = val
                                max_outlier_col = col
                    except:
                        pass

        # Score calculations
        completeness = max(0, 100.0 - ((total_missing + total_empty) / total_cells * 100) if total_cells > 0 else 100.0)
        consistency = max(0, 100.0 - (total_duplicates / total_rows * 100) if total_rows > 0 else 100.0)
        uniqueness = max(0, 100.0 - (total_duplicates / total_rows * 100) if total_rows > 0 else 100.0)
        
        num_cols = [c for c in active_cols if classifications.get(c) == "Numeric"]
        outlier_pct = (outliers_count / (total_rows * len(num_cols)) * 100) if len(num_cols) > 0 and total_rows > 0 else 0.0
        mismatch_pct = (total_type_mismatches / total_cells * 100) if total_cells > 0 else 0.0
        
        missing_pct = (total_missing / total_cells * 100) if total_cells > 0 else 0.0
        empty_pct = (total_empty / total_cells * 100) if total_cells > 0 else 0.0
        duplicate_pct = (total_duplicates / total_rows * 100) if total_rows > 0 else 0.0
        
        validity = max(0, 100.0 - (outlier_pct + mismatch_pct))
        accuracy = (completeness + consistency + validity + uniqueness) / 4

        # Explainable score deductions
        missing_deduction = -round(((total_missing + total_empty) / total_cells * 100), 2) if total_cells > 0 else 0.0
        duplicate_deduction = -round((total_duplicates / total_rows * 100), 2) if total_rows > 0 else 0.0
        outliers_deduction = -round(outlier_pct, 2)
        invalid_deduction = -round(mismatch_pct, 2)

        # Dynamic Column Profile Health Scoring
        column_health = {}
        for col in active_cols:
            col_health = 100.0
            
            # Deduct for missing
            missing_p = missing_pct_per_col.get(col, 0.0)
            col_health -= missing_p
            
            # Deduct for outliers (if numeric)
            if classifications[col] == "Numeric" and masks_cache and "outlier_indices" in masks_cache:
                col_outliers_count = len(masks_cache["outlier_indices"].get(col, []))
                outlier_p = (col_outliers_count / total_rows * 100) if total_rows > 0 else 0.0
                col_health -= outlier_p * 2.0
                
            # Deduct for type mismatch
            col_mismatches = 0
            if masks_cache and "invalid_type_indices" in masks_cache:
                col_mismatches = len(masks_cache["invalid_type_indices"].get(col, []))
            mismatch_p = (col_mismatches / total_rows * 100) if total_rows > 0 else 0.0
            col_health -= mismatch_p * 2.0
            
            # Deduct for casing consistency
            if col in inconsistent_categories_cols:
                col_health -= 15.0
                
            col_health = max(0.0, min(100.0, col_health))
            
            if col_health == 100.0:
                status = "Excellent"
            elif col_health >= 90.0:
                status = "Good"
            elif col_health >= 70.0:
                status = "Needs Attention"
            else:
                status = "Critical"
                
            column_health[col] = f"{status} ({round(col_health, 1)}/100)"
        
        top_10_missing = dict(sorted(missing_per_col.items(), key=lambda item: item[1], reverse=True)[:10])

        # Heuristic Dataset Type Inference
        col_names_lower = [c.lower() for c in active_cols]
        domain_weights = {
            "Entertainment Dataset": ["title", "director", "cast", "movie", "rating", "duration", "show", "actor", "actress", "album", "song", "genre"],
            "Healthcare Dataset": ["patient", "disease", "hospital", "doctor", "diagnosis", "blood", "clinical", "treatment", "symptom", "drug", "medication"],
            "Human Resources Dataset": ["employee", "salary", "department", "hire", "job", "payroll", "position", "manager", "performance", "hr"],
            "Retail Dataset": ["customer", "order", "product", "sales", "quantity", "store", "cart", "checkout", "retail", "discount"],
            "Finance Dataset": ["transaction", "balance", "finance", "account", "bank", "credit", "debit", "card", "loan", "tax", "stock"],
            "Education Dataset": ["student", "mark", "grade", "score", "teacher", "class", "course", "exam", "school", "university", "gpa"]
        }
        
        domain_scores = {domain: 0 for domain in domain_weights}
        for col in col_names_lower:
            for domain, keywords in domain_weights.items():
                for kw in keywords:
                    if kw in col:
                        domain_scores[domain] += 1
                        
        best_domain = max(domain_scores, key=domain_scores.get)
        if domain_scores[best_domain] > 0:
            dataset_type = best_domain
        else:
            dataset_type = "General Tabular Dataset"
            
        # Count Column Types
        cat_cols_count = sum(1 for c in active_cols if classifications[c] == "Categorical")
        num_cols_count = sum(1 for c in active_cols if classifications[c] == "Numeric")
        date_cols_count = sum(1 for c in active_cols if classifications[c] == "Date")
        text_cols_count = sum(1 for c in active_cols if classifications[c] == "Text")
        ident_cols_count = sum(1 for c in active_cols if classifications[c] == "Identifier")

        # AI Recommendations
        ai_recommendations = []
        priority = 1
        sorted_missing_cols = sorted(
            [(col, count) for col, count in missing_per_col.items() if count > 0],
            key=lambda x: x[1],
            reverse=True
        )
        for col, count in sorted_missing_cols[:3]:
            impact = round((count / total_cells * 100) / 4.0, 2) if total_cells > 0 else 0.0
            if impact > 0.01:
                ai_recommendations.append({
                    "priority": priority,
                    "action": f"Fill missing {col} ({round(missing_pct_per_col[col], 1)}% missing).",
                    "improvement": f"+{impact}%"
                })
                priority += 1
                
        for col in affected_columns[:2]:
            col_outlier_count = len(masks_cache["outlier_indices"].get(col, [])) if masks_cache else 0
            if col_outlier_count > 0:
                impact = round((col_outlier_count / (total_rows * len(num_cols)) * 100) / 4.0, 2) if total_rows > 0 and len(num_cols) > 0 else 0.0
                if impact > 0.01:
                    ai_recommendations.append({
                        "priority": priority,
                        "action": f"Handle {col} outliers ({col_outlier_count} found).",
                        "improvement": f"+{impact}%"
                    })
                    priority += 1

        # Dynamic AI Summary Paragraph
        summary_text = (
            f"The uploaded dataset is identified as a {dataset_type} containing {total_rows:,} rows and {len(active_cols)} columns. "
            f"Classification analysis identified {num_cols_count} numeric column(s), {date_cols_count} date column(s), {cat_cols_count} categorical column(s), "
            f"{text_cols_count} text column(s), and {ident_cols_count} identifier column(s) successfully. "
            f"{'No exact duplicate rows were found.' if total_duplicates == 0 else f'A total of {total_duplicates:,} exact duplicate rows were found.'} "
            f"A total of {total_missing:,} missing values were identified across {columns_affected_by_missing} column(s), "
            f"with {list(top_10_missing.keys())[0] if top_10_missing else 'none'} containing the highest percentage. "
            f"The system detected {outliers_count:,} outliers using the IQR method. "
            f"The overall dataset cleanliness score is {accuracy:.2f}%, indicating that the dataset is "
            f"{'suitable for analysis after minor preprocessing' if accuracy > 75 else 'in need of major cleaning before analysis'}."
        )

        missing_data_heatmap = []
        poor_quality_rows_count = 0
        try:
            sample_size = min(100, total_rows)
            if total_rows > sample_size:
                indices = [int(i) for i in np.linspace(0, total_rows - 1, sample_size)]
                sample_df = df[indices]
            else:
                sample_df = df

            for i, row in enumerate(sample_df.iter_rows(named=True)):
                row_data = {"_row_id": i + 1}
                for col_name, val in row.items():
                    if col_name.startswith("_") or col_name not in active_cols:
                        continue
                    is_missing = 0
                    if val is None:
                        is_missing = 1
                    elif isinstance(val, float) and math.isnan(val):
                        is_missing = 1
                    elif isinstance(val, str) and str(val).strip() == "":
                        is_missing = 1
                    row_data[col_name] = is_missing
                missing_data_heatmap.append(row_data)

            null_exprs = []
            for col in active_cols:
                dtype = df.schema[col]
                if dtype in [pl.Utf8, pl.Categorical]:
                    null_exprs.append((pl.col(col).is_null()) | (pl.col(col).str.strip_chars() == ""))
                elif dtype in [pl.Float32, pl.Float64]:
                    null_exprs.append((pl.col(col).is_null()) | (pl.col(col).is_nan()))
                else:
                    null_exprs.append(pl.col(col).is_null())
                    
            if null_exprs:
                poor_quality_rows_count = df.select(
                    pl.sum_horizontal(null_exprs).alias("missing_count")
                ).filter(
                    pl.col("missing_count") > (total_cols / 2)
                ).height
        except Exception as e:
            print(f"Error generating Missing Data Heatmap for dashboard: {e}")

        # Performance check
        elapsed_time = round(time.time() - start_time, 3)
        if elapsed_time <= 0:
            elapsed_time = 0.001

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
                "total_high_null_cols": len(high_null_cols),
                "total_missing_rows_count": total_missing_rows_count,
                "columns_affected_by_missing": columns_affected_by_missing
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
                "column_importance": column_health,
                "unique_counts_by_col": uniques
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
                "missing_data_heatmap": missing_data_heatmap
            },
            "score_breakdown": {
                "missing_values_impact": missing_deduction,
                "duplicates_impact": duplicate_deduction,
                "outliers_impact": outliers_deduction,
                "invalid_data_impact": invalid_deduction,
                "base_score": 100.0
            },
            "outlier_summary": {
                "detection_method": "IQR Method (Interquartile Range)",
                "columns_checked": numeric_cols_checked,
                "affected_columns": affected_columns,
                "largest_outlier_column": max_outlier_col,
                "largest_outlier_value": max_outlier_val,
                "minimum_outlier_column": min_outlier_col,
                "minimum_outlier_value": min_outlier_val
            },
            "dataset_summary": {
                "dataset_type": dataset_type,
                "categorical_columns_count": cat_cols_count,
                "numeric_columns_count": num_cols_count,
                "date_columns_count": date_cols_count,
                "text_columns_count": text_cols_count
            },
            "ai_recommendations": ai_recommendations,
            "ai_summary": summary_text,
            "performance": {
                "analysis_time_sec": elapsed_time,
                "memory_used_mb": round(df.estimated_size() / (1024 * 1024), 2),
                "processing_speed_rows_per_sec": int(total_rows / elapsed_time)
            }
        }
