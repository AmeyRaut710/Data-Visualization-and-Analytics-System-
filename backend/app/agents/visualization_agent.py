import pandas as pd
import logging
import math
import numpy as np

logger = logging.getLogger(__name__)

class VisualizationAgent:
    def __init__(self):
        pass
        
    def _is_id_column(self, col: str, df: pd.DataFrame) -> bool:
        col_lower = str(col).lower()
        if 'id' in col_lower or 'uuid' in col_lower or 'guid' in col_lower or 'hash' in col_lower or col_lower == 'index':
            if df[col].nunique() == len(df) or df[col].nunique() > 0.9 * len(df):
                return True
        return False
        
    def generate_visualizations(self, df: pd.DataFrame) -> list:
        valid_cols = [c for c in df.columns if not self._is_id_column(c, df)]
        if not valid_cols:
             return [{"error": "No valid columns found for visualization after excluding ID columns."}]
             
        df_valid = df[valid_cols]
        
        numerical_cols = df_valid.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
        categorical_cols = df_valid.select_dtypes(include=['object', 'category', 'string', 'bool']).columns.tolist()
        date_cols = df_valid.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
        
        visualizations = []
        
        def safe_float(val):
            try:
                v = float(val)
                if math.isnan(v) or math.isinf(v):
                    return 0.0
                return v
            except:
                return 0.0

        def safe_int(val):
            try:
                return int(val)
            except:
                return 0

        try:
            # 1. Correlation Heatmap & Scatter Plots (using highest correlations)
            if len(numerical_cols) >= 2:
                # Compute correlation matrix
                corr_matrix = df_valid[numerical_cols].corr().round(2).fillna(0)
                
                # Extract upper triangle pairs to find top correlations for scatter plots
                pairs = []
                for i in range(len(numerical_cols)):
                    for j in range(i+1, len(numerical_cols)):
                        col1 = numerical_cols[i]
                        col2 = numerical_cols[j]
                        val = corr_matrix.loc[col1, col2]
                        pairs.append((col1, col2, val))
                        
                # Sort by absolute correlation to find strongest relationships
                pairs.sort(key=lambda x: abs(x[2]), reverse=True)
                
                # Heatmap Insight
                strongest_pair = pairs[0] if pairs else None
                heatmap_insight = ""
                if strongest_pair and abs(strongest_pair[2]) > 0.3:
                    direction = "positive" if strongest_pair[2] > 0 else "negative"
                    heatmap_insight = f"The strongest correlation in the dataset is a {direction} relationship ({strongest_pair[2]}) between {strongest_pair[0]} and {strongest_pair[1]}."
                else:
                    heatmap_insight = "Most numerical variables show weak or no linear correlation with each other."

                # Add Heatmap
                data_points = []
                for i, row_col in enumerate(corr_matrix.columns):
                    for j, col_col in enumerate(corr_matrix.columns):
                        data_points.append({
                            "x": str(col_col),
                            "y": str(row_col),
                            "value": safe_float(corr_matrix.iloc[i, j])
                        })
                visualizations.append({
                    "chart_type": "heatmap",
                    "x_axis_column": "ALL_NUMERICAL",
                    "y_axis_column": "ALL_NUMERICAL",
                    "relevance_score": 95,
                    "chart_purpose": "Correlation Heatmap",
                    "key_findings": "Matrix of linear relationships between all numerical variables.",
                    "business_meaning": heatmap_insight,
                    "data": data_points
                })
                
                # Top 3 Scatter Plots based on highest correlations
                for pair in pairs[:3]:
                    xcol, ycol, corr_val = pair
                    if abs(corr_val) < 0.1: # Skip if virtually no correlation even among the "top"
                        continue
                        
                    sample_size = min(2000, len(df_valid))
                    sample_df = df_valid[[xcol, ycol]].dropna().sample(n=sample_size, random_state=42)
                    
                    data_points = []
                    for _, row in sample_df.iterrows():
                        data_points.append({
                            str(xcol): safe_float(row[xcol]),
                            str(ycol): safe_float(row[ycol])
                        })
                        
                    direction = "positive" if corr_val > 0 else "negative"
                    strength = "strong" if abs(corr_val) > 0.6 else "moderate" if abs(corr_val) > 0.3 else "weak"
                    
                    visualizations.append({
                        "chart_type": "scatter",
                        "x_axis_column": str(xcol),
                        "y_axis_column": str(ycol),
                        "relevance_score": int(80 + abs(corr_val)*20), # higher corr = higher relevance
                        "chart_purpose": f"{ycol} vs {xcol}",
                        "key_findings": f"Scatter plot showing the distribution between {ycol} and {xcol}.",
                        "trend_summary": f"There is a {strength} {direction} correlation (r={corr_val}) between these variables.",
                        "data": data_points
                    })
                
            # 2. Histograms (Top 5 numerical cols by highest variance)
            if numerical_cols:
                # Sort numerical columns by coefficient of variation (std/mean) to find most "interesting" distributions
                col_vars = []
                for col in numerical_cols:
                    mean_val = df_valid[col].mean()
                    if pd.notna(mean_val) and mean_val != 0:
                        cv = abs(df_valid[col].std() / mean_val)
                        col_vars.append((col, cv))
                
                col_vars.sort(key=lambda x: x[1], reverse=True)
                top_num_cols = [c[0] for c in col_vars[:5]] if col_vars else numerical_cols[:5]
                
                for xcol in top_num_cols:
                    hist, bin_edges = pd.cut(df_valid[xcol], bins=20, retbins=True)
                    counts = hist.value_counts().sort_index()
                    
                    max_idx = counts.argmax()
                    peak_start = bin_edges[max_idx]
                    peak_end = bin_edges[max_idx+1]
                    peak_pct = (counts.iloc[max_idx] / len(df_valid.dropna(subset=[xcol]))) * 100
                    
                    data_points = []
                    for i in range(len(counts)):
                        data_points.append({
                            str(xcol): f"{safe_float(bin_edges[i]):.1f} - {safe_float(bin_edges[i+1]):.1f}",
                            "count": safe_int(counts.iloc[i])
                        })
                        
                    visualizations.append({
                        "chart_type": "histogram",
                        "x_axis_column": str(xcol),
                        "y_axis_column": "count",
                        "relevance_score": 90,
                        "chart_purpose": f"Distribution of {xcol}",
                        "key_findings": f"Histogram showing the frequency distribution of {xcol}.",
                        "business_meaning": f"The most common range is between {safe_float(peak_start):.2f} and {safe_float(peak_end):.2f}, containing {peak_pct:.1f}% of the data.",
                        "data": data_points
                    })
                
            # 3. Categorical Bar / Pie (Top 5 categorical cols)
            # Sort categorical columns by uniqueness (fewer unique values = better pie chart, but skip if only 1 value)
            valid_cats = [c for c in categorical_cols if 1 < df_valid[c].nunique() <= 50]
            
            for cat_col in valid_cats[:5]:
                nunique = df_valid[cat_col].nunique()
                ctype = "pie" if nunique <= 6 else "bar"
                counts = df_valid[cat_col].value_counts().reset_index().head(20)
                
                top_cat = counts.iloc[0][cat_col]
                if pd.isna(top_cat) or str(top_cat).strip() == '':
                    top_cat_display = "Empty/Missing"
                else:
                    top_cat_display = str(top_cat)
                    
                top_count = counts.iloc[0]['count']
                total_valid = counts['count'].sum()
                top_pct = (top_count / total_valid) * 100 if total_valid > 0 else 0
                
                data_points = []
                for _, row in counts.iterrows():
                    cat_val = row[cat_col]
                    display_val = "Empty/Missing" if pd.isna(cat_val) or str(cat_val).strip() == '' else str(cat_val)
                    data_points.append({
                        str(cat_col): display_val,
                        "count": safe_int(row['count'])
                    })
                    
                visualizations.append({
                    "chart_type": ctype,
                    "x_axis_column": str(cat_col),
                    "y_axis_column": "count",
                    "relevance_score": 85 if ctype == "pie" else 80,
                    "chart_purpose": f"Top Categories in {cat_col}",
                    "key_findings": f"Breakdown of frequencies within {cat_col}.",
                    "business_meaning": f"'{top_cat_display}' is the dominant category, accounting for {top_pct:.1f}% of the top occurrences.",
                    "data": data_points
                })
                
            # 4. Time Series (Line) for all combinations of Date and top 3 Numeric
            if len(date_cols) >= 1 and len(numerical_cols) >= 1:
                xcol = date_cols[0] # Just use the first date column
                
                for ycol in numerical_cols[:3]:
                    grouped = df_valid.groupby(pd.Grouper(key=xcol, freq='ME'))[ycol].mean().reset_index()
                    if len(grouped) < 2:
                        continue # Not enough data points over time
                        
                    first_val = grouped.iloc[0][ycol]
                    last_val = grouped.iloc[-1][ycol]
                    max_idx = grouped[ycol].idxmax()
                    peak_date = grouped.iloc[max_idx][xcol]
                    
                    pct_change = 0
                    if pd.notna(first_val) and first_val != 0:
                        pct_change = ((last_val - first_val) / first_val) * 100
                    
                    direction = "increased" if pct_change > 0 else "decreased"
                    
                    data_points = []
                    for _, row in grouped.iterrows():
                        data_points.append({
                            str(xcol): str(row[xcol].strftime('%Y-%m-%d')) if pd.notna(row[xcol]) else "Unknown",
                            str(ycol): safe_float(row[ycol])
                        })
                        
                    visualizations.append({
                        "chart_type": "line",
                        "x_axis_column": str(xcol),
                        "y_axis_column": str(ycol),
                        "relevance_score": 92,
                        "chart_purpose": f"Trend of Average {ycol} over Time",
                        "key_findings": f"Time series analysis tracking {ycol}.",
                        "trend_summary": f"Overall, {ycol} has {direction} by {abs(pct_change):.1f}%, peaking on {peak_date.strftime('%Y-%m-%d') if pd.notna(peak_date) else 'Unknown'}.",
                        "data": data_points
                    })
                
            # 5. Stacked Bar (Top 2 Categorical against each other)
            if len(valid_cats) >= 2:
                xcol = valid_cats[0]
                ycol = valid_cats[1]
                
                if df_valid[ycol].nunique() <= 10 and df_valid[xcol].nunique() <= 20:
                    cross = pd.crosstab(df_valid[xcol], df_valid[ycol]).head(20)
                    
                    data_points = []
                    for idx, row in cross.iterrows():
                        point = {str(xcol): str(idx)}
                        for c in cross.columns:
                            point[str(c)] = safe_int(row[c])
                        data_points.append(point)
                        
                    visualizations.append({
                        "chart_type": "stacked_bar",
                        "x_axis_column": str(xcol),
                        "y_axis_column": str(ycol),
                        "relevance_score": 82,
                        "chart_purpose": f"{xcol} segmented by {ycol}",
                        "key_findings": f"Stacked breakdown of {xcol} frequencies sub-categorized by {ycol}.",
                        "business_meaning": f"Visualizes the interplay and distribution share between {xcol} and {ycol}.",
                        "sub_categories": [str(c) for c in cross.columns],
                        "data": data_points
                    })
                
        except Exception as e:
            logger.error(f"Error in offline heuristics: {str(e)}")
            visualizations.append({"error": f"Heuristic visualization engine failed: {str(e)}"})
            
        # Sort by relevance to show the most interesting charts first
        visualizations = sorted(visualizations, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        if not visualizations:
            visualizations.append({"error": "Failed to mathematically derive any meaningful relationships from the dataset."})
            
        return visualizations
