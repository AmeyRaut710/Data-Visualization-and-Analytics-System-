import pandas as pd
import logging

logger = logging.getLogger(__name__)

class InsightAgent:
    def __init__(self):
        # Deterministic offline engine initialized without API keys
        pass

    def generate_insights(self, df: pd.DataFrame) -> list:
        insights = []
        try:
            num_rows = len(df)
            num_cols = len(df.columns)
            
            # 1. Structural Insight
            insights.append(f"The dataset contains a matrix of {num_rows:,} rows and {num_cols} columns.")
            
            # 2. Data Cleanliness
            missing_count = int(df.isna().sum().sum())
            missing_percent = (missing_count / (num_rows * num_cols)) * 100 if num_rows * num_cols > 0 else 0
            if missing_count > 0:
                insights.append(f"There are {missing_count:,} missing values across the dataset, representing {missing_percent:.1f}% of total cells. Data cleaning is recommended.")
            else:
                insights.append("The dataset is extremely clean with 0 missing or null values detected.")
                
            # 3. Categorical Dominance
            cat_cols = df.select_dtypes(include=['object', 'category', 'string', 'bool']).columns
            for col in cat_cols:
                if df[col].nunique() > 0:
                    top_val = df[col].mode().iloc[0]
                    top_freq = (df[col] == top_val).sum()
                    top_pct = (top_freq / num_rows) * 100
                    if top_pct > 70 and top_pct < 100:
                        insights.append(f"Categorical dominance detected: '{col}' is heavily skewed towards the value '{top_val}' ({top_pct:.1f}% of rows).")
                        break # Just one categorical insight is enough
                        
            # 4. Numerical Skewness or Range
            num_cols_list = df.select_dtypes(include=['int64', 'float64']).columns
            for col in num_cols_list:
                skewness = df[col].skew()
                if pd.notna(skewness) and abs(skewness) > 1.5:
                    direction = "positively" if skewness > 0 else "negatively"
                    insights.append(f"Distribution skew detected: '{col}' is heavily {direction} skewed (skew={skewness:.2f}), suggesting the presence of outliers.")
                    break
            
            # 5. Low Cardinality Flags
            for col in num_cols_list:
                unique_vals = df[col].nunique()
                if unique_vals == 2:
                    insights.append(f"Feature engineering hint: The numerical column '{col}' contains exactly 2 unique values, suggesting it should be treated as a boolean or categorical flag.")
                    break
                    
            # Fallback if we didn't reach 5 insights
            if len(insights) < 5 and len(num_cols_list) > 0:
                insights.append(f"Statistical baseline: The primary metric '{num_cols_list[0]}' averages {df[num_cols_list[0]].mean():.2f} with a maximum of {df[num_cols_list[0]].max():.2f}.")
                
            return insights[:5]
            
        except Exception as e:
            logger.error(f"Error in offline heuristics: {str(e)}")
            return [f"Heuristic insight engine failed: {str(e)}"]

    def generate_health_report(self, quality: dict) -> dict:
        metrics = quality.get("metrics", {})
        scores = quality.get("scores", {})
        anomalies = quality.get("anomalies", {})
        
        total_rows = metrics.get("total_rows", 0)
        total_cols = metrics.get("total_cols", 0)
        total_missing = metrics.get("total_missing_values", 0)
        total_empty = metrics.get("total_empty_cells", 0)
        missing_pct = scores.get("missing_pct", 0)
        empty_pct = scores.get("empty_pct", 0)
        completeness = scores.get("completeness", 0)
        
        strengths = []
        if metrics.get("total_exact_duplicates", 0) == 0:
            strengths.append("No duplicate records detected.")
        if metrics.get("total_outliers", 0) == 0:
            strengths.append("No outliers detected.")
        if total_missing <= 10:
            strengths.append(f"Only {total_missing} missing value(s) detected.")
        if total_empty == 0:
            strengths.append("No empty cells detected.")
            
        if len(strengths) == 0:
            strengths.append("Dataset has been successfully parsed.")

        issues = []
        if total_empty > 0:
            issues.append(f"{total_empty:,} empty cells detected ({empty_pct:.2f}%).")
        if total_missing > 10:
            issues.append(f"{total_missing:,} missing values detected ({missing_pct:.2f}%).")
        if len(anomalies.get("high_empty_cols", [])) > 0:
            issues.append(f"Several columns ({len(anomalies.get('high_empty_cols', []))}) have >30% empty values.")
        if metrics.get("total_exact_duplicates", 0) > 0:
            issues.append(f"{metrics.get('total_exact_duplicates', 0):,} duplicate rows detected.")
        
        if total_empty > 0 or total_missing > 0:
            issues.append("Data quality may affect visualizations and predictions.")
            
        if len(issues) == 0:
            issues.append("No major issues detected.")

        actions = []
        if len(anomalies.get("high_empty_cols", [])) > 0:
            actions.append("Review columns with >30% empty values.")
        if anomalies.get("poor_quality_rows_count", 0) > 0:
            actions.append("Fill or remove highly incomplete records.")
        if metrics.get("total_exact_duplicates", 0) > 0:
            actions.append("Remove exact duplicate rows.")
        if metrics.get("total_outliers", 0) > 0:
            actions.append("Investigate outlier values in numeric columns.")
            
        actions.append("Recalculate quality score after cleaning.")
            
        overall = "Excellent" if completeness >= 90 else "Good" if completeness >= 80 else "Average" if completeness >= 70 else "Poor"
        
        return {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "strengths": strengths,
            "issues": issues,
            "actions": actions,
            "overall_quality": overall,
            "completeness_score": completeness
        }
