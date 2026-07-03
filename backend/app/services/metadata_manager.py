import polars as pl
import numpy as np

class MetadataManager:
    @staticmethod
    def _normalize_for_duplicates(df: pl.DataFrame) -> pl.DataFrame:
        MISSING_VALUES_SET = {'null', 'nan', 'none', 'na', 'n/a', '#n/a', 'nat', '?'}
        norm_exprs = []
        for col in df.columns:
            dtype = df.schema[col]
            if dtype in [pl.Utf8, pl.Categorical]:
                stripped = pl.col(col).str.strip_chars()
                is_missing = stripped.str.to_lowercase().is_in(list(MISSING_VALUES_SET))
                norm_exprs.append(
                    pl.when(is_missing).then(None)
                      .otherwise(stripped).alias(col)
                )
            elif dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                norm_exprs.append(pl.col(col).cast(pl.Float64, strict=False).alias(col))
            else:
                norm_exprs.append(pl.col(col))
        return df.with_columns(norm_exprs)

    @staticmethod
    def compute_all_masks(df: pl.DataFrame, ignored_issues: dict = None) -> tuple[dict, pl.DataFrame]:
        # 1. Exact Duplicates with Pre-Standardization
        norm_df = MetadataManager._normalize_for_duplicates(df)
        
        # Group by all columns to find identical rows
        grouped = norm_df.with_row_index("idx").group_by(df.columns, maintain_order=True).agg(pl.col("idx"))
        dup_groups = grouped.filter(pl.col("idx").list.len() > 1).get_column("idx").to_list()
        
        # Flatten groups to get all duplicate indices
        global_dups_idx = [idx for group in dup_groups for idx in group]
        
        outlier_indices = {}
        empty_indices = {}
        missing_indices = {}
        invalid_type_indices = {}
        inconsistent_cat_indices = {}
        stats = {}
        
        MISSING_VALUES_SET = {'null', 'nan', 'none', 'na', 'n/a', '#n/a', 'nat', '?'}
        
        cast_exprs = []
        
        # Pass 1: Strings (Missing, Empty, Numeric Inference)
        for col in df.columns:
            dtype = df.schema[col]
            stats[col] = {}
            
            if dtype in [pl.Utf8, pl.Categorical]:
                is_missing = (pl.col(col).is_null()) | (pl.col(col).cast(pl.Utf8).str.strip_chars().str.to_lowercase().is_in(list(MISSING_VALUES_SET)))
                is_empty = (pl.col(col).is_not_null()) & (pl.col(col).cast(pl.Utf8).str.strip_chars() == "")
                
                missing_idx = df.with_row_index("idx").filter(is_missing).get_column("idx").to_list()
                if missing_idx: missing_indices[col] = missing_idx
                
                empty_idx = df.with_row_index("idx").filter(is_empty).get_column("idx").to_list()
                if empty_idx: empty_indices[col] = empty_idx
                
                s = df.get_column(col)
                # valid elements excluding missing/empty
                valid_mask = s.is_not_null() & ~s.str.strip_chars().str.to_lowercase().is_in(list(MISSING_VALUES_SET)) & (s.str.strip_chars() != "")
                valid_s = s.filter(valid_mask)
                valid_count = len(valid_s)
                
                if valid_count > 0:
                    num_count = valid_s.str.contains(r'^-?\d+\.?\d*$').sum()
                    if num_count / valid_count >= 0.9:
                        cast_exprs.append(pl.col(col).cast(pl.Float64, strict=False))
                    else:
                        try: stats[col]['mode'] = valid_s.mode()[0]
                        except: pass
            else:
                if dtype in [pl.Float32, pl.Float64]:
                    is_missing = pl.col(col).is_null() | pl.col(col).is_nan()
                else:
                    is_missing = pl.col(col).is_null()
                is_empty = pl.lit(False)
                missing_idx = df.with_row_index("idx").filter(is_missing).get_column("idx").to_list()
                if missing_idx: missing_indices[col] = missing_idx
                empty_idx = df.with_row_index("idx").filter(is_empty).get_column("idx").to_list()
                if empty_idx: empty_indices[col] = empty_idx

        # Perform Casts
        if cast_exprs:
            df = df.with_columns(cast_exprs)
            
        # Pass 2: Numeric stats, Outliers, Invalid Type, Inconsistent Categories
        for col in df.columns:
            dtype = df.schema[col]
            
            if dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                s = df.get_column(col).drop_nulls()
                if len(s) > 0:
                    stats[col]['mean'] = s.mean()
                    stats[col]['median'] = s.median()
                    try: stats[col]['mode'] = s.mode()[0]
                    except: pass
                    stats[col]['std'] = s.std()
                
                if len(s) >= 10:
                    q1 = s.quantile(0.25)
                    q3 = s.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    
                    stats[col].update({
                        'q1': q1, 'q3': q3, 'iqr': iqr, 
                        'lower': lower, 'upper': upper,
                        'p5': s.quantile(0.05),
                        'p90': s.quantile(0.90),
                        'p95': s.quantile(0.95)
                    })
                    
                    method = 'IQR'
                    is_large = len(s) > 50000
                    skew_val = s.skew()
                    is_normal = skew_val is not None and abs(skew_val) < 0.5
                    
                    if is_large and is_normal:
                        method = 'Z-Score'
                        
                    if method == 'IQR':
                        is_outlier = (pl.col(col) < lower) | (pl.col(col) > upper)
                        stats[col]['outlier_method'] = 'IQR'
                        stats[col]['lower_bound'] = float(lower)
                        stats[col]['upper_bound'] = float(upper)
                    else:
                        mean = stats[col]['mean']
                        std = stats[col]['std']
                        if std is not None and std > 0:
                            is_outlier = ((pl.col(col) - mean) / std).abs() > 3
                            stats[col]['outlier_method'] = 'Z-Score'
                            stats[col]['lower_bound'] = float(mean - 3 * std)
                            stats[col]['upper_bound'] = float(mean + 3 * std)
                        else:
                            is_outlier = pl.lit(False)
                            stats[col]['outlier_method'] = 'None'
                            stats[col]['lower_bound'] = None
                            stats[col]['upper_bound'] = None
                            
                    outlier_idx = df.with_row_index("idx").filter(is_outlier).get_column("idx").to_list()
                    if outlier_idx: outlier_indices[col] = outlier_idx

            if dtype in [pl.Utf8, pl.Categorical]:
                valid_df = df.select([pl.col(col).alias("val")]).filter(pl.col("val").is_not_null() & (pl.col("val").cast(pl.Utf8).str.strip_chars() != ""))
                valid_count = valid_df.height
                if valid_count > 0:
                    sample_size = min(valid_count, 2000)
                    sample_df = valid_df.head(sample_size)
                    
                    num_count = sample_df.filter(pl.col("val").cast(pl.Utf8).str.contains(r'^-?\d+\.?\d*$')).height
                    email_count = sample_df.filter(pl.col("val").cast(pl.Utf8).str.contains(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')).height
                    phone_count = sample_df.filter(pl.col("val").cast(pl.Utf8).str.contains(r'^\+?[\d\s\-\(\)]{7,15}$')).height
                    
                    invalid_expr = None
                    if num_count / sample_size > 0.8:
                        invalid_expr = (pl.col(col).is_not_null()) & (pl.col(col).cast(pl.Utf8).str.strip_chars() != "") & (~pl.col(col).cast(pl.Utf8).str.contains(r'^-?\d+\.?\d*$'))
                    elif email_count / sample_size > 0.8:
                        invalid_expr = (pl.col(col).is_not_null()) & (pl.col(col).cast(pl.Utf8).str.strip_chars() != "") & (~pl.col(col).cast(pl.Utf8).str.contains(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'))
                    elif phone_count / sample_size > 0.8:
                        invalid_expr = (pl.col(col).is_not_null()) & (pl.col(col).cast(pl.Utf8).str.strip_chars() != "") & (~pl.col(col).cast(pl.Utf8).str.contains(r'^\+?[\d\s\-\(\)]{7,15}$'))
                        
                    if invalid_expr is not None:
                        invalid_idx = df.with_row_index("idx").filter(invalid_expr).get_column("idx").to_list()
                        if invalid_idx: invalid_type_indices[col] = invalid_idx
                        
                    original_uniques = valid_df.get_column("val").n_unique()
                    if 0 < original_uniques < 1000:
                        lower_uniques = valid_df.get_column("val").cast(pl.Utf8).str.to_lowercase().n_unique()
                        if lower_uniques < original_uniques:
                            counts_dicts = valid_df.group_by("val").agg(pl.count("val").alias("count")).sort("count", descending=True).to_dicts()
                            dominant_casing = {}
                            for row in counts_dicts:
                                val_str = str(row["val"])
                                val_lower = val_str.lower()
                                if val_lower not in dominant_casing:
                                    dominant_casing[val_lower] = val_str
                            
                            inconsistent_vals = []
                            for val in valid_df.get_column("val").unique().to_list():
                                val_str = str(val)
                                if val_str != dominant_casing.get(val_str.lower(), val_str):
                                    inconsistent_vals.append(val)
                                    
                            if inconsistent_vals:
                                inconsistent_idx = df.with_row_index("idx").filter(pl.col(col).cast(pl.Utf8).is_in(inconsistent_vals)).get_column("idx").to_list()
                                if inconsistent_idx: inconsistent_cat_indices[col] = inconsistent_idx

        if ignored_issues:
            for issue_name, cols in ignored_issues.items():
                if issue_name == "Missing Values":
                    for c in cols:
                        if c == "all": missing_indices.clear()
                        elif c in missing_indices: del missing_indices[c]
                elif issue_name == "Empty Cells":
                    for c in cols:
                        if c == "all": empty_indices.clear()
                        elif c in empty_indices: del empty_indices[c]
                elif issue_name == "Outliers":
                    for c in cols:
                        if c == "all": outlier_indices.clear()
                        elif c in outlier_indices: del outlier_indices[c]
                elif issue_name in ["Duplicate Rows", "Exact Duplicates"]:
                    if "all" in cols:
                        global_dups_idx.clear()
                        dup_groups.clear()

        cache = {
            "stats": stats,
            "dup_groups": dup_groups,
            "global_dups_idx": global_dups_idx,
            "outlier_indices": outlier_indices,
            "empty_indices": empty_indices,
            "missing_indices": missing_indices,
            "invalid_type_indices": invalid_type_indices,
            "inconsistent_cat_indices": inconsistent_cat_indices
        }
        return cache, df

    @staticmethod
    def update_masks(df: pl.DataFrame, cache: dict, issue: str, columns: list, ignored_issues: dict = None) -> tuple[dict, pl.DataFrame]:
        cols_to_process = columns if columns and len(columns) > 0 and columns[0] != 'all' else df.columns

        missing_cols = [c for c in cols_to_process if c not in df.columns]
        if missing_cols:
            for k in ["outlier_indices", "empty_indices", "missing_indices", "invalid_type_indices", "inconsistent_cat_indices"]:
                if k in cache:
                    for c in missing_cols:
                        if c in cache[k]:
                            del cache[k][c]
            cols_to_process = [c for c in cols_to_process if c in df.columns]
            
        if not cols_to_process and missing_cols:
            return cache, df

        drops_rows = issue in ['Duplicate Rows', 'Exact Duplicates', 'Business Duplicates', 'Near Duplicates', 'Manual Removal', 'Delete Rows containing Missing Values', 'Remove Rows containing Empty Cells', 'Remove Outlier Rows']
        
        if issue in ["Missing Values", "Empty Cells", "Outliers", "Inconsistent Categories", "Invalid Data Types", "Extra Spaces", "Special Characters", "Constant Columns", "High Cardinality", "Inconsistent Format", "Date Format Problems"] and not drops_rows:
            partial_df = df.select(cols_to_process)
            partial_cache, partial_df_typed = MetadataManager.compute_all_masks(partial_df, ignored_issues)
            
            typed_cols = []
            for col in df.columns:
                if col in cols_to_process:
                    typed_cols.append(partial_df_typed.get_column(col))
                else:
                    typed_cols.append(df.get_column(col))
            df = pl.DataFrame(typed_cols)

            for k in ["outlier_indices", "empty_indices", "missing_indices", "invalid_type_indices", "inconsistent_cat_indices"]:
                if k not in cache: cache[k] = {}
                for c in cols_to_process:
                    if c in partial_cache.get(k, {}):
                        cache[k][c] = partial_cache[k][c]
                    elif c in cache[k]:
                        del cache[k][c]
                        
            if "stats" not in cache: cache["stats"] = {}
            for c in cols_to_process:
                if c in partial_cache.get("stats", {}):
                    cache["stats"][c] = partial_cache["stats"][c]
                        
        else:
            return MetadataManager.compute_all_masks(df, ignored_issues)
            
        return cache, df
