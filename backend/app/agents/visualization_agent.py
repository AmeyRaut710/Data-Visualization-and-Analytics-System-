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
        MAX_VISUALIZATIONS = 150 # Global cap to ensure high performance
        
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
            # 1. Correlation Heatmap
            if len(numerical_cols) >= 2:
                # Limit to top 30 numerical cols for heatmap to avoid overwhelming the UI
                heat_cols = numerical_cols[:30]
                sample_size_corr = min(10000, len(df_valid))
                corr_matrix = df_valid[heat_cols].sample(n=sample_size_corr, random_state=42).corr().round(2).fillna(0)
                
                pairs = []
                for i in range(len(heat_cols)):
                    for j in range(i+1, len(heat_cols)):
                        col1 = heat_cols[i]
                        col2 = heat_cols[j]
                        val = corr_matrix.loc[col1, col2]
                        pairs.append((col1, col2, val))
                        
                pairs.sort(key=lambda x: abs(x[2]), reverse=True)
                
                strongest_pair = pairs[0] if pairs else None
                heatmap_insight = ""
                if strongest_pair and abs(strongest_pair[2]) > 0.3:
                    direction = "positive" if strongest_pair[2] > 0 else "negative"
                    heatmap_insight = f"The strongest correlation in the dataset is a {direction} relationship ({strongest_pair[2]}) between {strongest_pair[0]} and {strongest_pair[1]}."
                else:
                    heatmap_insight = "Most numerical variables show weak or no linear correlation with each other."

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
                    "key_findings": "Matrix of linear relationships between numerical variables.",
                    "business_meaning": heatmap_insight,
                    "data": data_points
                })
                
                # Top Scatter Plots (Filtered by Threshold)
                for pair in pairs:
                    xcol, ycol, corr_val = pair
                    if abs(corr_val) < 0.15: # RELEVANCE THRESHOLD
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
                        "relevance_score": int(70 + abs(corr_val)*30),
                        "chart_purpose": f"{ycol} vs {xcol}",
                        "key_findings": f"Scatter plot showing how {ycol} behaves in relation to {xcol}.",
                        "trend_summary": f"There is a {strength} {direction} correlation (r={corr_val}) meaning as {xcol} increases, {ycol} tends to {'increase' if corr_val > 0 else 'decrease'}.",
                        "data": data_points
                    })
                
            # 2. Histograms (All Numerical columns)
            if numerical_cols:
                for xcol in numerical_cols:
                    hist, bin_edges = pd.cut(df_valid[xcol], bins=20, retbins=True)
                    counts = hist.value_counts().sort_index()
                    
                    if len(counts) == 0 or len(df_valid.dropna(subset=[xcol])) == 0:
                        continue
                        
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
                        "relevance_score": 85,
                        "chart_purpose": f"Distribution of {xcol}",
                        "key_findings": f"Visualizes the spread and shape of {xcol} data points.",
                        "business_meaning": f"The most common range of {xcol} falls between {safe_float(peak_start):.2f} and {safe_float(peak_end):.2f}, accounting for {peak_pct:.1f}% of all records.",
                        "data": data_points
                    })
                
            # 3. Categorical Bar / Pie / Donut (All valid categorical cols)
            valid_cats = [c for c in categorical_cols if 1 < df_valid[c].nunique() <= 50]
            
            for i, cat_col in enumerate(valid_cats):
                nunique = df_valid[cat_col].nunique()
                if nunique <= 6:
                    ctype = "pie" if i % 2 == 0 else "donut"
                else:
                    ctype = "bar"
                    
                counts = df_valid[cat_col].value_counts().reset_index().head(20)
                if len(counts) == 0: continue
                
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
                    "relevance_score": 80,
                    "chart_purpose": f"Distribution of {cat_col}",
                    "key_findings": f"Breakdown of how often different categories appear in {cat_col}.",
                    "business_meaning": f"'{top_cat_display}' is the dominant category, representing {top_pct:.1f}% of the occurrences.",
                    "data": data_points
                })
                
            # 4. Time Series (Line / Area) for Date vs Numerical
            if len(date_cols) >= 1 and len(numerical_cols) >= 1:
                for xcol in date_cols:
                    for i, ycol in enumerate(numerical_cols):
                        grouped = df_valid.groupby(pd.Grouper(key=xcol, freq='ME'))[ycol].mean().reset_index()
                        if len(grouped) < 2:
                            continue
                            
                        first_val = grouped.iloc[0][ycol]
                        last_val = grouped.iloc[-1][ycol]
                        max_idx = grouped[ycol].idxmax()
                        peak_date = grouped.iloc[max_idx][xcol]
                        
                        pct_change = 0
                        if pd.notna(first_val) and first_val != 0:
                            pct_change = ((last_val - first_val) / first_val) * 100
                        
                        # Only show trend if variance is somewhat notable (e.g. > 5% change or high stdev)
                        std_dev = grouped[ycol].std()
                        mean_v = grouped[ycol].mean()
                        cv = abs(std_dev / mean_v) if mean_v != 0 else 0
                        
                        if cv < 0.05 and abs(pct_change) < 5:
                            continue # Ignore highly flat lines
                        
                        direction = "increased" if pct_change > 0 else "decreased"
                        ctype = "area" if i % 2 == 0 else "line"
                        
                        data_points = []
                        for _, row in grouped.iterrows():
                            data_points.append({
                                str(xcol): str(row[xcol].strftime('%Y-%m-%d')) if pd.notna(row[xcol]) else "Unknown",
                                str(ycol): safe_float(row[ycol])
                            })
                            
                        visualizations.append({
                            "chart_type": ctype,
                            "x_axis_column": str(xcol),
                            "y_axis_column": str(ycol),
                            "relevance_score": int(80 + min(20, cv * 50)),
                            "chart_purpose": f"Trend of Average {ycol} over Time",
                            "key_findings": f"Chronological tracking of how the average {ycol} changes.",
                            "trend_summary": f"Over the recorded period, {ycol} has {direction} by {abs(pct_change):.1f}%, peaking on {peak_date.strftime('%Y-%m-%d') if pd.notna(peak_date) else 'Unknown'}.",
                            "data": data_points
                        })
                
            # 5. Stacked Bar / Grouped Bar (Categorical vs Categorical cross-tabs)
            if len(valid_cats) >= 2:
                for i in range(len(valid_cats)):
                    for j in range(i+1, len(valid_cats)):
                        xcol = valid_cats[i]
                        ycol = valid_cats[j]
                        
                        # Only plot if number of categories is manageable for a grouped bar
                        if df_valid[ycol].nunique() <= 10 and df_valid[xcol].nunique() <= 15:
                            cross = pd.crosstab(df_valid[xcol], df_valid[ycol]).head(15)
                            
                            data_points = []
                            for idx, row in cross.iterrows():
                                point = {str(xcol): str(idx)}
                                for c in cross.columns:
                                    point[str(c)] = safe_int(row[c])
                                data_points.append(point)
                                
                            ctype = "stacked_bar" if (i+j) % 2 == 0 else "grouped_bar"
                            visualizations.append({
                                "chart_type": ctype,
                                "x_axis_column": str(xcol),
                                "y_axis_column": str(ycol),
                                "relevance_score": 75,
                                "chart_purpose": f"{xcol} segmented by {ycol}",
                                "key_findings": f"Breakdown of {xcol} frequencies sub-categorized by {ycol}.",
                                "business_meaning": f"Visualizes the interplay and distribution share between {xcol} and {ycol}.",
                                "sub_categories": [str(c) for c in cross.columns],
                                "data": data_points
                            })
                        
            # 6. Bar Charts (Categorical vs Numerical)
            if len(valid_cats) >= 1 and len(numerical_cols) >= 1:
                for xcol in valid_cats:
                    if df_valid[xcol].nunique() > 20: continue # Skip if too many categories
                    
                    for ycol in numerical_cols:
                        grouped = df_valid.groupby(xcol)[ycol].mean().reset_index().sort_values(by=ycol, ascending=False).head(20)
                        if len(grouped) == 0: continue
                        
                        max_cat = grouped.iloc[0][xcol]
                        max_val = grouped.iloc[0][ycol]
                        
                        data_points = []
                        for _, row in grouped.iterrows():
                            cat_val = row[xcol]
                            display_val = "Empty/Missing" if pd.isna(cat_val) or str(cat_val).strip() == '' else str(cat_val)
                            data_points.append({
                                str(xcol): display_val,
                                str(ycol): safe_float(row[ycol])
                            })
                            
                        # Only include if variance between groups is notable
                        cv = grouped[ycol].std() / grouped[ycol].mean() if grouped[ycol].mean() != 0 else 0
                        if abs(cv) > 0.05:
                            visualizations.append({
                                "chart_type": "bar",
                                "x_axis_column": str(xcol),
                                "y_axis_column": str(ycol),
                                "relevance_score": int(75 + min(25, abs(cv)*20)),
                                "chart_purpose": f"Average {ycol} across {xcol}",
                                "key_findings": f"Compares the average {ycol} value for different groups within {xcol}.",
                                "business_meaning": f"The category '{max_cat}' leads with the highest average {ycol} ({safe_float(max_val):.2f}).",
                                "data": data_points
                            })
                
        except Exception as e:
            logger.error(f"Error in offline heuristics: {str(e)}")
            visualizations.append({"error": f"Heuristic visualization engine failed: {str(e)}"})
            
        # Ensure highest scores stay within bound
        for v in visualizations:
            if 'relevance_score' in v:
                v['relevance_score'] = min(100, v['relevance_score'])
                
        visualizations = sorted(visualizations, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Apply performance cap
        visualizations = visualizations[:MAX_VISUALIZATIONS]
        
        if not visualizations:
            visualizations.append({"error": "Failed to mathematically derive any meaningful relationships from the dataset."})
            
        return visualizations
