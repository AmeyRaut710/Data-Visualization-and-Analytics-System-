import polars as pl
from app.services.data_quality import DataQualityService
import logging

logger = logging.getLogger(__name__)

class DataCleaningService:
    @staticmethod
    def apply_targeted_cleaning(pldf: pl.DataFrame, issue: str, columns: list, method: str, custom_value: str = None, cache: dict = None) -> pl.DataFrame:
        cols_to_process = columns if columns and len(columns) > 0 and columns[0] != 'all' else pldf.columns
        
        if method == 'Ignore':
            return pldf
            
        try:
            if issue == 'Missing Values':
                return DataCleaningService._clean_missing_values(pldf, cols_to_process, method, custom_value, cache)
            elif issue == 'Empty Cells':
                return DataCleaningService._clean_empty_cells(pldf, cols_to_process, method, custom_value, cache)
            elif issue == 'Outliers':
                return DataCleaningService._clean_outliers(pldf, cols_to_process, method, cache)
            elif issue in ['Duplicate Rows', 'Exact Duplicates', 'Business Duplicates', 'Near Duplicates']:
                return DataCleaningService._clean_duplicates(pldf, cols_to_process, method, cache)
            elif issue == 'Extra Spaces' and method == 'Trim Spaces':
                return DataCleaningService._clean_extra_spaces(pldf, cols_to_process)
            elif issue == 'Special Characters' and method == 'Remove Special Characters':
                return DataCleaningService._clean_special_chars(pldf, cols_to_process)
            elif issue in ['Constant Columns', 'High Cardinality']:
                return DataCleaningService._clean_drop_columns(pldf, cols_to_process, method)
            elif issue == 'Invalid Data Types':
                return DataCleaningService._clean_invalid_types(pldf, cols_to_process, method)
            elif issue in ['Duplicate Columns', 'High Null Percentage Columns']:
                return DataCleaningService._clean_drop_columns(pldf, cols_to_process, method)
            elif issue == 'Inconsistent Categories':
                return DataCleaningService._clean_inconsistent_categories(pldf, cols_to_process, method)
            elif issue == 'Date Format Problems':
                return DataCleaningService._clean_dates(pldf, cols_to_process, method)
            elif issue == 'Manual Removal':
                return DataCleaningService._clean_manual(pldf, cols_to_process, method, custom_value)
                
            return pldf
        except Exception as e:
            logger.error(f"Error applying {method} for {issue}: {str(e)}")
            return pldf

    @staticmethod
    def _clean_missing_values(pldf: pl.DataFrame, cols: list, method: str, custom_value: str, cache: dict):
        if method in ['Drop Rows', 'Delete Rows containing Missing Values']:
            missing_idx = []
            for col in cols:
                if cache and col in cache.get("missing_indices", {}):
                    missing_idx.extend(cache["missing_indices"][col])
            if missing_idx:
                return pldf.with_row_index("idx").filter(~pl.col("idx").is_in(set(missing_idx))).drop("idx")
            return pldf
            
        elif method in ['Drop Column', 'Delete Columns containing Missing Values']:
            return pldf.drop(cols)
            
        pldf = pldf.with_row_index("idx")
        exprs = []
        for col in cols:
            target_idx = set(cache.get("missing_indices", {}).get(col, [])) if cache else set()
            if not target_idx:
                continue
                
            if method == 'Replace with Custom Value':
                dtype = pldf.schema[col]
                if dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    try: val = float(custom_value)
                    except: val = None
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(val)).otherwise(pl.col(col)).alias(col))
                else:
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(custom_value or "Unknown")).otherwise(pl.col(col)).alias(col))
                    
            elif method == 'Fill with Mean' or method == 'Replace with Mean':
                if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    mean_val = cache.get("stats", {}).get(col, {}).get("mean") if cache else None
                    if mean_val is not None:
                        exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(mean_val)).otherwise(pl.col(col)).alias(col))
                        
            elif method == 'Fill with Median' or method == 'Replace with Median':
                if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    med_val = cache.get("stats", {}).get(col, {}).get("median") if cache else None
                    if med_val is not None:
                        exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(med_val)).otherwise(pl.col(col)).alias(col))
                        
            elif method == 'Fill with Mode' or method == 'Replace with Mode':
                mode_val = cache.get("stats", {}).get(col, {}).get("mode") if cache else None
                if mode_val is not None:
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(mode_val)).otherwise(pl.col(col)).alias(col))
                    
            elif method in ['Fill using Previous Value', 'Replace with Previous Value']:
                filled_col = pl.col(col).fill_null(strategy="forward")
                exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(filled_col).otherwise(pl.col(col)).alias(col))
                
            elif method in ['Fill using Next Value', 'Replace with Next Value']:
                filled_col = pl.col(col).fill_null(strategy="backward")
                exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(filled_col).otherwise(pl.col(col)).alias(col))
                
            elif method == 'Linear Interpolation':
                if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    filled_col = pl.col(col).interpolate()
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(filled_col).otherwise(pl.col(col)).alias(col))

        if exprs:
            pldf = pldf.with_columns(exprs)
            
        return pldf.drop("idx")

    @staticmethod
    def _clean_empty_cells(pldf: pl.DataFrame, cols: list, method: str, custom_value: str, cache: dict):
        if method in ['Remove Rows', 'Remove Rows containing Empty Cells']:
            empty_idx = []
            for col in cols:
                if cache and col in cache.get("empty_indices", {}):
                    empty_idx.extend(cache["empty_indices"][col])
            if empty_idx:
                return pldf.with_row_index("idx").filter(~pl.col("idx").is_in(set(empty_idx))).drop("idx")
            return pldf
            
        elif method == 'Remove Columns containing Empty Cells':
            return pldf.drop(cols)

        pldf = pldf.with_row_index("idx")
        exprs = []
        for col in cols:
            target_idx = set(cache.get("empty_indices", {}).get(col, [])) if cache else set()
            if not target_idx: continue
            
            if method == 'Trim Spaces':
                if pldf.schema[col] in [pl.Utf8, pl.Categorical]:
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.col(col).str.strip_chars()).otherwise(pl.col(col)).alias(col))
            elif method == 'Replace with NULL':
                exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(None).otherwise(pl.col(col)).alias(col))
            elif method == 'Replace with Custom Value':
                dtype = pldf.schema[col]
                if dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    try: val = float(custom_value)
                    except: val = None
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(val)).otherwise(pl.col(col)).alias(col))
                else:
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(custom_value or "Unknown")).otherwise(pl.col(col)).alias(col))
            elif method == 'Replace with Mode' or method == 'Fill with Mode':
                mode_val = cache.get("stats", {}).get(col, {}).get("mode") if cache else None
                if mode_val is not None:
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(mode_val)).otherwise(pl.col(col)).alias(col))
            elif method == 'Replace with Mean' or method == 'Fill with Mean':
                if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    mean_val = cache.get("stats", {}).get(col, {}).get("mean") if cache else None
                    if mean_val is not None:
                        exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(mean_val)).otherwise(pl.col(col)).alias(col))
            elif method == 'Replace with Median' or method == 'Fill with Median':
                if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    med_val = cache.get("stats", {}).get(col, {}).get("median") if cache else None
                    if med_val is not None:
                        exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(pl.lit(med_val)).otherwise(pl.col(col)).alias(col))
            elif method in ['Fill using Previous Value', 'Replace with Previous Value']:
                filled_col = pl.col(col).fill_null(strategy="forward")
                exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(filled_col).otherwise(pl.col(col)).alias(col))
            elif method in ['Fill using Next Value', 'Replace with Next Value']:
                filled_col = pl.col(col).fill_null(strategy="backward")
                exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(filled_col).otherwise(pl.col(col)).alias(col))
            elif method == 'Linear Interpolation':
                if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                    filled_col = pl.col(col).interpolate()
                    exprs.append(pl.when(pl.col("idx").is_in(target_idx)).then(filled_col).otherwise(pl.col(col)).alias(col))

        if exprs:
            pldf = pldf.with_columns(exprs)
            
        return pldf.drop("idx")

    @staticmethod
    def _clean_outliers(pldf: pl.DataFrame, cols: list, method: str, cache: dict):
        exprs = []
        filter_mask = None
        
        for col in cols:
            if pldf.schema[col] in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
                col_stats = cache.get("stats", {}).get(col) if cache else None
                
                if col_stats and "lower_bound" in col_stats and col_stats["lower_bound"] is not None:
                    lower = col_stats["lower_bound"]
                    upper = col_stats["upper_bound"]
                    mean = col_stats.get("mean")
                    med = col_stats.get("median")
                    std = col_stats.get("std")
                else:
                    s = pldf.get_column(col).drop_nulls()
                    if len(s) < 10: continue
                    q1 = s.quantile(0.25)
                    q3 = s.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    mean = s.mean()
                    med = s.median()
                    std = s.std()
                
                is_outlier = (pl.col(col) < lower) | (pl.col(col) > upper)
                
                if method in ['Remove Outliers', 'Remove Outlier Rows']:
                    col_mask = ~is_outlier | pl.col(col).is_null()
                    filter_mask = col_mask if filter_mask is None else filter_mask & col_mask
                elif method in ['Cap to Upper Bound', 'Cap Values', 'IQR Clipping']:
                    exprs.append(
                        pl.when(pl.col(col) > upper).then(pl.lit(upper))
                        .when(pl.col(col) < lower).then(pl.lit(lower))
                        .otherwise(pl.col(col)).alias(col)
                    )
                elif method == 'Winsorization':
                    p5 = col_stats.get("p5") if col_stats else pldf.get_column(col).drop_nulls().quantile(0.05)
                    p95 = col_stats.get("p95") if col_stats else pldf.get_column(col).drop_nulls().quantile(0.95)
                    exprs.append(
                        pl.when(pl.col(col) > p95).then(pl.lit(p95))
                        .when(pl.col(col) < p5).then(pl.lit(p5))
                        .otherwise(pl.col(col)).alias(col)
                    )
                elif method == 'Z-Score Clipping':
                    if std and std > 0:
                        z_lower = mean - 3 * std
                        z_upper = mean + 3 * std
                        exprs.append(
                            pl.when(pl.col(col) > z_upper).then(pl.lit(z_upper))
                            .when(pl.col(col) < z_lower).then(pl.lit(z_lower))
                            .otherwise(pl.col(col)).alias(col)
                        )
                elif method == 'Replace using Median':
                    exprs.append(pl.when(is_outlier).then(pl.lit(med)).otherwise(pl.col(col)).alias(col))
                elif method == 'Replace using Mean':
                    exprs.append(pl.when(is_outlier).then(pl.lit(mean)).otherwise(pl.col(col)).alias(col))
                elif method == 'Replace with Q1':
                    q1 = col_stats.get("q1") if col_stats else pldf.get_column(col).drop_nulls().quantile(0.25)
                    exprs.append(pl.when(is_outlier).then(pl.lit(q1)).otherwise(pl.col(col)).alias(col))
                elif method == 'Replace with Q3':
                    q3 = col_stats.get("q3") if col_stats else pldf.get_column(col).drop_nulls().quantile(0.75)
                    exprs.append(pl.when(is_outlier).then(pl.lit(q3)).otherwise(pl.col(col)).alias(col))
                elif method == 'Replace using Percentile':
                    p90 = col_stats.get("p90") if col_stats else pldf.get_column(col).drop_nulls().quantile(0.90)
                    exprs.append(pl.when(is_outlier).then(pl.lit(p90)).otherwise(pl.col(col)).alias(col))
                    
        if filter_mask is not None:
            pldf = pldf.filter(filter_mask)
        if exprs:
            pldf = pldf.with_columns(exprs)
            
        return pldf

    @staticmethod
    def _clean_duplicates(pldf: pl.DataFrame, cols: list, method: str, cache: dict):
        # Only use pre-computed exact duplicates if we are applying to ALL columns and issue is Exact Duplicates
        if cache and "dup_groups" in cache and (not cols or cols[0] == 'all' or len(cols) == pldf.width):
            dup_groups = cache["dup_groups"]
            indices_to_drop = []
            
            if method in ['Remove Exact Duplicates', 'Keep First Occurrence', 'Keep First', 'Merge Records', 'Merge Duplicate Records', 'Keep Most Complete Row']:
                for group in dup_groups:
                    indices_to_drop.extend(group[1:])
            elif method in ['Keep Latest Occurrence', 'Keep Last']:
                for group in dup_groups:
                    indices_to_drop.extend(group[:-1])
                    
            if indices_to_drop:
                pldf = pldf.with_row_index("idx_manual_drop")
                pldf = pldf.filter(~pl.col("idx_manual_drop").is_in(indices_to_drop)).drop("idx_manual_drop")
            return pldf
            
        # Fallback for column subsets or missing cache
        subset = cols if cols and cols[0] != 'all' else None
        if method in ['Remove Exact Duplicates', 'Keep First Occurrence', 'Keep First', 'Merge Records', 'Merge Duplicate Records', 'Keep Most Complete Row']:
            return pldf.unique(subset=subset, keep='first')
        elif method in ['Keep Latest Occurrence', 'Keep Last']:
            return pldf.unique(subset=subset, keep='last')
        return pldf

    @staticmethod
    def _clean_extra_spaces(pldf: pl.DataFrame, cols: list):
        exprs = []
        for col in cols:
            if pldf.schema[col] in [pl.Utf8, pl.Categorical]:
                exprs.append(pl.col(col).str.strip_chars().alias(col))
        if exprs: pldf = pldf.with_columns(exprs)
        return pldf

    @staticmethod
    def _clean_special_chars(pldf: pl.DataFrame, cols: list):
        exprs = []
        for col in cols:
            if pldf.schema[col] in [pl.Utf8, pl.Categorical]:
                exprs.append(pl.col(col).str.replace_all(r'[^\w\s\.\,\-\@\_]', '').alias(col))
        if exprs: pldf = pldf.with_columns(exprs)
        return pldf

    @staticmethod
    def _clean_drop_columns(pldf: pl.DataFrame, cols: list, method: str):
        if method in ['Drop Column', 'Drop Duplicate Columns', 'Drop Columns']:
            return pldf.drop(cols)
        return pldf

    @staticmethod
    def _clean_invalid_types(pldf: pl.DataFrame, cols: list, method: str):
        exprs = []
        for col in cols:
            if method == 'Convert to Numeric':
                exprs.append(pl.col(col).cast(pl.Float64, strict=False).alias(col))
            elif method == 'Convert to String':
                exprs.append(pl.col(col).cast(pl.Utf8).alias(col))
        if exprs: pldf = pldf.with_columns(exprs)
        return pldf
        
    @staticmethod
    def _clean_inconsistent_categories(pldf: pl.DataFrame, cols: list, method: str):
        exprs = []
        if method == 'Standardize Format':
            for col in cols:
                if pldf.schema[col] in [pl.Utf8, pl.Categorical]:
                    exprs.append(pl.col(col).str.to_lowercase().alias(col))
        if exprs: pldf = pldf.with_columns(exprs)
        return pldf
        
    @staticmethod
    def _clean_dates(pldf: pl.DataFrame, cols: list, method: str):
        exprs = []
        if method == 'Convert to Single Format':
            for col in cols:
                exprs.append(pl.col(col).str.strptime(pl.Datetime, strict=False).alias(col))
        if exprs: pldf = pldf.with_columns(exprs)
        return pldf
        
    @staticmethod
    def _clean_manual(pldf: pl.DataFrame, cols: list, method: str, custom_value: str):
        if method == 'Drop Column':
            return pldf.drop(cols)
        elif method == 'Drop Row':
            try:
                if custom_value:
                    idx_to_drop = [int(x.strip()) for x in str(custom_value).split(',')]
                    pldf = pldf.with_row_index("idx_manual_drop")
                    pldf = pldf.filter(~pl.col("idx_manual_drop").is_in(idx_to_drop)).drop("idx_manual_drop")
            except: pass
        return pldf
