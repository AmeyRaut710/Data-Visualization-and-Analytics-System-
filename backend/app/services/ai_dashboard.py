import polars as pl
from datetime import datetime
import json
import math

class AIDashboardService:
    @staticmethod
    def _detect_dataset_type(cols):
        col_lower = set([c.lower() for c in cols])
        if bool({"revenue", "price", "sales", "order", "cost"} & col_lower):
            return "Sales Dataset", "Sales Analytics Dashboard"
        elif bool({"patient", "disease", "hospital", "doctor", "diagnosis", "health"} & col_lower):
            return "Healthcare Dataset", "Healthcare Analytics Dashboard"
        elif bool({"movie", "title", "director", "genre", "rating", "cinema"} & col_lower):
            return "Movie Dataset", "Movie Insights Dashboard"
        elif bool({"student", "school", "grade", "class", "course"} & col_lower):
            return "Education Dataset", "Education Analytics Dashboard"
        elif bool({"employee", "salary", "hr", "manager", "department"} & col_lower):
            return "Employee Dataset", "HR & Employee Analytics Dashboard"
        elif bool({"account", "transaction", "bank", "credit", "loan"} & col_lower):
            return "Financial Dataset", "Financial Analytics Dashboard"
        elif bool({"sensor", "iot", "device", "temperature", "reading"} & col_lower):
            return "IoT Dataset", "IoT & Sensor Analytics Dashboard"
        else:
            return "General Tabular Dataset", "General Data Analytics Dashboard"

    @staticmethod
    def _is_id_column(col_name, dtype, unique_ratio):
        cl = col_name.lower()
        if "id" in cl or "uuid" in cl or "key" in cl:
            return True
        if dtype in [pl.String, pl.Utf8, pl.Int64, pl.Int32] and unique_ratio > 0.95:
            return True
        return False

    @staticmethod
    def generate_dashboard(df: pl.DataFrame, existing_charts=None):
        start_time = datetime.now()
        row_count = df.height
        
        # 17. Large Dataset Optimization
        if row_count > 100000:
            viz_df = df.sample(n=100000)
        else:
            viz_df = df

        # 16. Empty Dataset Handling
        if row_count == 0:
            return {
                "datasetType": "Empty Dataset",
                "title": "No Data Available",
                "generatedTime": datetime.now().isoformat(),
                "kpis": [],
                "charts": existing_charts if existing_charts else [],
                "insights": ["The dataset is empty after filtering."],
                "filters": [],
                "narrative": {"summary": "No data available matching filters.", "recommendations": []},
                "table": {"columns": [], "data": []}
            }

        # 1-3. Deep Metadata Profiling & Detection
        metadata = {}
        num_cols = []
        cat_cols = []
        date_cols = []
        bool_cols = []
        text_cols = []
        id_cols = []

        for col in df.columns:
            dtype = df.schema[col]
            s = df.get_column(col)
            null_count = s.null_count()
            null_pct = null_count / row_count if row_count else 0
            
            try:
                unique_count = s.n_unique()
            except:
                unique_count = row_count
                
            unique_ratio = unique_count / row_count if row_count else 0
            
            is_id = AIDashboardService._is_id_column(col, dtype, unique_ratio)
            col_type = "unknown"

            if is_id:
                col_type = "id"
                id_cols.append(col)
            elif dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64, pl.Float32, pl.Float64]:
                col_type = "numeric"
                num_cols.append(col)
            elif dtype in [pl.Date, pl.Datetime]:
                col_type = "date"
                date_cols.append(col)
            elif dtype == pl.Boolean:
                col_type = "boolean"
                bool_cols.append(col)
            elif dtype in [pl.Categorical, pl.String, pl.Utf8]:
                if unique_count < 50 or unique_ratio < 0.05:
                    col_type = "categorical"
                    cat_cols.append(col)
                else:
                    col_type = "text"
                    text_cols.append(col)
            
            metadata[col] = {
                "type": col_type,
                "null_pct": null_pct,
                "unique_count": unique_count,
                "unique_ratio": unique_ratio
            }

        dataset_type, dashboard_title = AIDashboardService._detect_dataset_type(df.columns)

        # 4. Smart KPIs
        kpis = []
        kpis.append({"title": "Total Rows", "value": f"{row_count:,}", "prefix": "", "suffix": ""})
        kpis.append({"title": "Total Columns", "value": str(len(df.columns)), "prefix": "", "suffix": ""})
        
        # Add dynamic numeric KPIs
        sorted_num = sorted([c for c in num_cols if metadata[c]["null_pct"] < 0.5], key=lambda x: metadata[x]["unique_count"], reverse=True)
        for col in sorted_num[:4]:
            s = df.get_column(col).drop_nulls()
            if s.len() > 0:
                val = s.sum()
                prefix = "$" if any(k in col.lower() for k in ["revenue", "price", "cost", "salary", "profit"]) else ""
                
                if val > 1_000_000_000:
                    val_str = f"{val/1_000_000_000:.1f}B"
                elif val > 1_000_000:
                    val_str = f"{val/1_000_000:.1f}M"
                elif val > 1_000:
                    val_str = f"{val/1_000:.1f}K"
                else:
                    val_str = str(round(val, 2))
                kpis.append({"title": f"Total {col}", "value": val_str, "prefix": prefix, "suffix": ""})
                
                # Also add average for top 2
                if len(kpis) < 8:
                    avg_val = s.mean()
                    if avg_val > 1_000_000_000:
                        avg_str = f"{avg_val/1_000_000_000:.1f}B"
                    elif avg_val > 1_000_000:
                        avg_str = f"{avg_val/1_000_000:.1f}M"
                    elif avg_val > 1_000:
                        avg_str = f"{avg_val/1_000:.1f}K"
                    else:
                        avg_str = str(round(avg_val, 2))
                    kpis.append({"title": f"Avg {col}", "value": avg_str, "prefix": prefix, "suffix": ""})

        # Top Categorical KPI
        if cat_cols:
            top_cat = sorted(cat_cols, key=lambda x: metadata[x]["unique_count"], reverse=True)[0]
            kpis.append({"title": f"Unique {top_cat}s", "value": str(metadata[top_cat]["unique_count"]), "prefix": "", "suffix": ""})

        kpis = kpis[:8]

        # 5, 6, 9, 11: Intelligent Chart Selection & Explainable AI
        charts = []
        
        if existing_charts:
            # Refresh data for existing charts to prevent layout shift
            for chart in existing_charts:
                try:
                    c_type = chart["type"]
                    c_id = chart["id"]
                    if c_type == "bar" and chart.get("x_axis") in cat_cols:
                        col = chart["x_axis"]
                        vc = viz_df.get_column(col).value_counts().sort("count", descending=True).head(10)
                        chart["data"] = vc.to_dicts()
                    elif c_type == "pie" and chart.get("name_key") in cat_cols:
                        col = chart["name_key"]
                        vc = viz_df.get_column(col).value_counts().sort("count", descending=True)
                        chart["data"] = vc.to_dicts()
                    elif c_type == "bar" and chart.get("x_axis") == "bin": # Histogram
                        # We would need the original column name, which we might not have explicitly in chart. 
                        # Let's extract from title: "Distribution of {col}"
                        col = chart["title"].replace("Distribution of ", "")
                        if col in num_cols:
                            s = viz_df.get_column(col).drop_nulls()
                            if s.len() > 0:
                                min_val, max_val = s.min(), s.max()
                                if min_val != max_val:
                                    bins = 10
                                    bin_size = (max_val - min_val) / bins
                                    hist_data = []
                                    for i in range(bins):
                                        lower = min_val + i * bin_size
                                        upper = min_val + (i + 1) * bin_size if i < bins - 1 else max_val
                                        count = s.filter((s >= lower) & (s <= upper)).len()
                                        hist_data.append({"bin": f"{lower:.1f}-{upper:.1f}", "count": count})
                                    chart["data"] = hist_data
                    elif c_type == "line" and chart.get("x_axis") in date_cols and chart.get("y_axis") in num_cols:
                        d_col = chart["x_axis"]
                        n_col = chart["y_axis"]
                        agg = viz_df.group_by(d_col).agg(pl.col(n_col).sum()).sort(d_col)
                        if agg.height > 100:
                             agg = agg.sample(n=100).sort(d_col)
                        
                        data = []
                        for row in agg.to_dicts():
                            d = row[d_col]
                            row[d_col] = d.strftime("%Y-%m-%d") if isinstance(d, datetime) else str(d)
                            data.append(row)
                        chart["data"] = data
                    elif c_type == "scatter" and chart.get("x_axis") in num_cols and chart.get("y_axis") in num_cols:
                        x_col = chart["x_axis"]
                        y_col = chart["y_axis"]
                        sample = viz_df.sample(n=min(viz_df.height, 200)).drop_nulls(subset=[x_col, y_col])
                        chart["data"] = sample.select([x_col, y_col]).to_dicts()
                    elif c_type == "area" and chart.get("x_axis") in cat_cols and chart.get("y_axis") in num_cols:
                        c_col = chart["x_axis"]
                        n_col = chart["y_axis"]
                        agg = viz_df.group_by(c_col).agg(pl.col(n_col).sum()).sort(n_col, descending=True)
                        chart["data"] = agg.to_dicts()
                    charts.append(chart)
                except Exception as e:
                    pass
        else:
            chart_id_counter = 1
            
            # Categorical Bar Charts
            for col in sorted(cat_cols, key=lambda x: metadata[x]["unique_count"])[:3]: # Max 3 bar charts
                uc = metadata[col]["unique_count"]
                if 2 <= uc <= 20:
                    vc = viz_df.get_column(col).value_counts().sort("count", descending=True).head(10)
                    data = vc.to_dicts()
                    charts.append({
                        "id": f"chart_{chart_id_counter}",
                        "type": "bar",
                        "title": f"Top {col} by Count",
                        "data": data,
                        "x_axis": col,
                        "y_axis": "count",
                        "score": 10 - uc/5, # Higher score for fewer categories
                        "reason": f"Selected Bar Chart because '{col}' has low cardinality ({uc} unique values), ideal for categorical comparison."
                    })
                    chart_id_counter += 1
                    
            # Pie Chart
            for col in cat_cols:
                uc = metadata[col]["unique_count"]
                if 2 <= uc <= 8:
                    vc = viz_df.get_column(col).value_counts().sort("count", descending=True)
                    charts.append({
                        "id": f"chart_{chart_id_counter}",
                        "type": "pie",
                        "title": f"{col} Distribution",
                        "data": vc.to_dicts(),
                        "name_key": col,
                        "value_key": "count",
                        "score": 9,
                        "reason": f"Selected Pie Chart because '{col}' has {uc} categories (<= 8), perfect for showing part-to-whole relationships."
                    })
                    chart_id_counter += 1
                    break # Only 1 pie chart

            # Numeric Histogram
            for col in num_cols[:2]:
                s = viz_df.get_column(col).drop_nulls()
                if s.len() > 10:
                    min_val, max_val = s.min(), s.max()
                    if min_val != max_val:
                        bins = 10
                        bin_size = (max_val - min_val) / bins
                        hist_data = []
                        for i in range(bins):
                            lower = min_val + i * bin_size
                            upper = min_val + (i + 1) * bin_size if i < bins - 1 else max_val
                            count = s.filter((s >= lower) & (s <= upper)).len()
                            hist_data.append({"bin": f"{lower:.1f}-{upper:.1f}", "count": count})
                        charts.append({
                            "id": f"chart_{chart_id_counter}",
                            "type": "bar", 
                            "title": f"Distribution of {col}",
                            "data": hist_data,
                            "x_axis": "bin",
                            "y_axis": "count",
                            "score": 8.5,
                            "reason": f"Selected Histogram because '{col}' is a numeric continuous variable, revealing its underlying distribution shape."
                        })
                        chart_id_counter += 1

            # Date Line Chart (Time Series)
            if date_cols and num_cols:
                d_col = date_cols[0]
                n_col = num_cols[0]
                agg = viz_df.group_by(d_col).agg(pl.col(n_col).sum()).sort(d_col)
                if agg.height > 100:
                     agg = agg.sample(n=100).sort(d_col)
                
                data = []
                for row in agg.to_dicts():
                    d = row[d_col]
                    row[d_col] = d.strftime("%Y-%m-%d") if isinstance(d, datetime) else str(d)
                    data.append(row)
                    
                charts.append({
                    "id": f"chart_{chart_id_counter}",
                    "type": "line",
                    "title": f"{n_col} Over Time ({d_col})",
                    "data": data,
                    "x_axis": d_col,
                    "y_axis": n_col,
                    "score": 9.5,
                    "reason": f"Selected Line Chart because '{d_col}' provides chronological context, perfect for tracking '{n_col}' trends over time."
                })
                chart_id_counter += 1

            # Scatter Plot (Correlation)
            if len(num_cols) >= 2:
                x_col = num_cols[0]
                y_col = num_cols[1]
                sample = viz_df.sample(n=min(viz_df.height, 200)).drop_nulls(subset=[x_col, y_col])
                charts.append({
                    "id": f"chart_{chart_id_counter}",
                    "type": "scatter",
                    "title": f"{y_col} vs {x_col}",
                    "data": sample.select([x_col, y_col]).to_dicts(),
                    "x_axis": x_col,
                    "y_axis": y_col,
                    "score": 8.0,
                    "reason": f"Selected Scatter Plot to visualize the potential correlation and variance between '{x_col}' and '{y_col}'."
                })
                chart_id_counter += 1

            # Area Chart (Numeric vs Category)
            if len(cat_cols) > 0 and len(num_cols) > 0:
                c_col = cat_cols[0]
                n_col = num_cols[-1]
                if metadata[c_col]["unique_count"] <= 15:
                    agg = viz_df.group_by(c_col).agg(pl.col(n_col).sum()).sort(n_col, descending=True)
                    charts.append({
                        "id": f"chart_{chart_id_counter}",
                        "type": "area",
                        "title": f"Total {n_col} by {c_col}",
                        "data": agg.to_dicts(),
                        "x_axis": c_col,
                        "y_axis": n_col,
                        "score": 8.8,
                        "reason": f"Selected Area Chart to highlight the accumulated volume of '{n_col}' across different '{c_col}' segments."
                    })
                    chart_id_counter += 1

            # Sort charts by score and keep top 8
            charts = sorted(charts, key=lambda x: x.get("score", 0), reverse=True)[:8]

        # 10. Smart Filters
        filters = []
        for col in cat_cols[:4]:
            if metadata[col]["unique_count"] <= 50:
                unique_vals = viz_df.get_column(col).drop_nulls().unique().to_list()
                filters.append({
                    "column": col,
                    "type": "category",
                    "options": [str(v) for v in unique_vals[:50]]
                })
                
        for col in num_cols[:2]:
            min_val = viz_df.get_column(col).min()
            max_val = viz_df.get_column(col).max()
            if min_val is not None and max_val is not None and min_val != max_val:
                filters.append({
                    "column": col,
                    "type": "numeric",
                    "min": float(min_val),
                    "max": float(max_val)
                })

        # 8 & 15. AI Insights & Narrative
        insights = []
        insights.append(f"Analyzed {row_count:,} rows and {len(df.columns)} columns in {(datetime.now() - start_time).total_seconds():.2f}s.")
        
        if cat_cols:
            c = cat_cols[0]
            top_val = viz_df.get_column(c).value_counts().sort("count", descending=True)[c][0]
            insights.append(f"'{top_val}' dominates the {c} category, representing the highest frequency.")
            
        if num_cols:
            n = num_cols[0]
            avg = viz_df.get_column(n).mean()
            if avg is not None:
                insights.append(f"The average {n} across the dataset is {avg:,.2f}.")
                
        if len(num_cols) >= 2:
            insights.append(f"Potential multidimensional relationships exist between {num_cols[0]} and {num_cols[1]}.")

        missing_total = sum(metadata[c]["null_pct"] for c in metadata)
        if missing_total > 0:
            worst_col = max(metadata.keys(), key=lambda x: metadata[x]["null_pct"])
            if metadata[worst_col]["null_pct"] > 0:
                insights.append(f"Data quality remark: '{worst_col}' has the highest missing value rate ({metadata[worst_col]['null_pct']*100:.1f}%).")
        else:
            insights.append("Data quality is excellent with no significant missing values detected in key columns.")

        executive_summary = f"This {dataset_type} contains {row_count:,} records across {len(df.columns)} dimensions. "
        if num_cols:
            executive_summary += f"Key metrics include {', '.join(num_cols[:3])}. "
        if cat_cols:
            executive_summary += f"Data is segmented primarily by {', '.join(cat_cols[:2])}. "
        
        recommendations = [
            f"Focus strategic efforts on the top-performing '{cat_cols[0]}' segments to maximize impact." if cat_cols else "Analyze individual row anomalies.",
            f"Investigate outliers in '{num_cols[0]}' to understand extreme variance." if num_cols else "Enhance dataset with numerical KPIs.",
            "Utilize the interactive filters above to drill down into specific timeframes and categories."
        ]

        # Table data
        table_cols = df.columns[:10]
        table_data = viz_df.select(table_cols).head(50).to_dicts()
        for r in table_data:
            for k, v in r.items():
                if isinstance(v, datetime):
                    r[k] = v.isoformat()
                elif v != v:
                    r[k] = None

        layout = {
            "title": dashboard_title,
            "datasetType": dataset_type,
            "generatedTime": datetime.now().isoformat(),
            "kpis": kpis,
            "charts": charts,
            "insights": insights,
            "filters": filters,
            "narrative": {
                "summary": executive_summary,
                "recommendations": recommendations
            },
            "table": {
                "columns": table_cols,
                "data": table_data
            }
        }
        
        return layout
