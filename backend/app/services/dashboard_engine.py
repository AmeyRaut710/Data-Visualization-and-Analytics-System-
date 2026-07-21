import polars as pl
import json
import uuid
import math
from typing import Dict, List, Any

class PowerBIDashboardEngine:
    """
    Analyzes a dataframe (or set of dataframes) and automatically generates
    a comprehensive Power BI style dashboard configuration including KPIs, 
    charts, filters, and AI insights.
    """

    @staticmethod
    def _classify_columns(df: pl.DataFrame) -> Dict[str, str]:
        """Classifies each column into a semantic type."""
        classifications = {}
        for col in df.columns:
            dtype = df.schema[col]
            if dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64]:
                if col.lower().endswith("id") or col.lower() == "id":
                    classifications[col] = "Identifier"
                elif "year" in col.lower() and df.get_column(col).drop_nulls().min() >= 1900 and df.get_column(col).drop_nulls().max() <= 2100:
                    classifications[col] = "Date"
                else:
                    classifications[col] = "Numeric"
            elif dtype in [pl.Date, pl.Datetime]:
                classifications[col] = "Date"
            elif dtype == pl.String:
                s = df.get_column(col).drop_nulls()
                if len(s) == 0:
                    classifications[col] = "Empty"
                    continue
                # Simple check for geospatial
                geo_keywords = ["city", "country", "state", "region", "zip", "location", "address"]
                is_geo = any(g in col.lower() for g in geo_keywords)
                
                unique_count = s.n_unique()
                total_count = len(s)
                
                if is_geo and unique_count < 1000:
                    classifications[col] = "Geo"
                elif unique_count == total_count:
                    classifications[col] = "Identifier"
                elif unique_count <= 20:
                    classifications[col] = "Categorical_LowCard"
                elif unique_count <= 1000:
                    classifications[col] = "Categorical_HighCard"
                else:
                    classifications[col] = "Text"
            elif dtype in [pl.Boolean]:
                classifications[col] = "Boolean"
                # Handled above
                pass
        return classifications

    @staticmethod
    def _generate_kpis(df: pl.DataFrame, classifications: Dict[str, str]) -> List[Dict[str, Any]]:
        kpis = []
        cols_lower = [c.lower() for c in df.columns]
        
        # 13 Domain Detection Heuristics
        domain = "Generic"
        domain_keywords = {
            "Sales": ["revenue", "sales", "profit", "order", "price", "discount"],
            "Finance": ["income", "expense", "roi", "margin", "tax", "budget", "ledger"],
            "Healthcare": ["patient", "disease", "diagnosis", "doctor", "blood", "heart", "age"],
            "Customer": ["customer", "churn", "loyalty", "ltv", "nps", "subscriber"],
            "HR": ["employee", "department", "salary", "hire_date", "attrition", "role"],
            "Education": ["student", "grade", "school", "course", "exam", "teacher"],
            "Retail": ["product", "category", "inventory", "stock", "store"],
            "Survey": ["response", "satisfaction", "rating", "feedback", "question"],
            "IoT/Sensor": ["sensor", "device", "temperature", "reading", "telemetry", "voltage"],
            "Logistics": ["shipment", "delivery", "freight", "warehouse", "route", "carrier"],
            "Marketing": ["campaign", "click", "impression", "conversion", "lead", "cpc"],
            "Manufacturing": ["machine", "downtime", "yield", "defect", "production", "assembly"],
            "Movies": ["movie", "director", "cast", "genre", "season", "episode"]
        }
        
        for d, keywords in domain_keywords.items():
            if any(w in cols_lower for w in keywords):
                domain = d
                break
                
        # Basic KPIs
        kpis.append({"id": str(uuid.uuid4()), "title": f"Total {domain if domain != 'Generic' else 'Records'}", "value": df.height, "type": "count", "format": "number"})
        
        numeric_cols = [c for c, t in classifications.items() if t == "Numeric"]
        cat_cols = [c for c, t in classifications.items() if t in ["Categorical_LowCard", "Categorical_HighCard"]]
        
        if domain == "Movies":
            type_col = next((c for c in df.columns if "type" in c.lower()), None)
            if type_col:
                movies_count = df.filter(pl.col(type_col).str.to_lowercase().str.contains("movie")).height
                tv_count = df.filter(pl.col(type_col).str.to_lowercase().str.contains("tv")).height
                if movies_count > 0: kpis.append({"id": str(uuid.uuid4()), "title": "Total Movies", "value": movies_count, "type": "count", "format": "number"})
                if tv_count > 0: kpis.append({"id": str(uuid.uuid4()), "title": "TV Shows", "value": tv_count, "type": "count", "format": "number"})
            year_col = next((c for c in df.columns if "year" in c.lower()), None)
            if year_col and year_col in numeric_cols:
                avg_year = df.get_column(year_col).drop_nulls().mean()
                if avg_year: kpis.append({"id": str(uuid.uuid4()), "title": "Avg Release Year", "value": round(avg_year), "type": "average", "format": "number"})
        elif domain == "Sales" or domain == "Retail":
            revenue_col = next((c for c in numeric_cols if "revenue" in c.lower() or "sales" in c.lower()), None)
            if revenue_col:
                total_rev = df.get_column(revenue_col).drop_nulls().sum()
                kpis.append({"id": str(uuid.uuid4()), "title": "Total Revenue", "value": round(total_rev, 2), "type": "sum", "format": "currency"})
            profit_col = next((c for c in numeric_cols if "profit" in c.lower()), None)
            if profit_col:
                total_prof = df.get_column(profit_col).drop_nulls().sum()
                kpis.append({"id": str(uuid.uuid4()), "title": "Total Profit", "value": round(total_prof, 2), "type": "sum", "format": "currency"})
            if domain == "Retail":
                prod_col = next((c for c in df.columns if "product" in c.lower()), None)
                if prod_col:
                    kpis.append({"id": str(uuid.uuid4()), "title": "Unique Products", "value": df.get_column(prod_col).n_unique(), "type": "count", "format": "number"})
        elif domain == "HR":
            emp_col = next((c for c in df.columns if "employee" in c.lower() or "emp_id" in c.lower()), None)
            if emp_col:
                kpis.append({"id": str(uuid.uuid4()), "title": "Total Employees", "value": df.get_column(emp_col).n_unique(), "type": "count", "format": "number"})
            dept_col = next((c for c in df.columns if "department" in c.lower()), None)
            if dept_col:
                kpis.append({"id": str(uuid.uuid4()), "title": "Departments", "value": df.get_column(dept_col).n_unique(), "type": "count", "format": "number"})
        elif domain == "Survey":
            sat_col = next((c for c in df.columns if "satisfaction" in c.lower() or "rating" in c.lower()), None)
            if sat_col and sat_col in numeric_cols:
                avg_sat = df.get_column(sat_col).drop_nulls().mean()
                if avg_sat: kpis.append({"id": str(uuid.uuid4()), "title": "Avg Satisfaction", "value": round(avg_sat, 1), "type": "average", "format": "number"})
        
        # Generic fill
        for col in numeric_cols:
            if len(kpis) >= 6: break
            if any(col.lower() in kpi["title"].lower() for kpi in kpis): continue
            s = df.get_column(col).drop_nulls()
            if len(s) == 0: continue
            
            total = s.sum()
            avg = s.mean()
            kpi_type = "sum" if any(w in col.lower() for w in ["sales", "revenue", "profit", "count", "total"]) else "average"
            val = total if kpi_type == "sum" else avg
            fmt = "currency" if any(w in col.lower() for w in ["price", "sales", "revenue", "profit", "cost", "salary"]) else "number"
            
            if isinstance(val, float): val = round(val, 2)
            kpis.append({"id": str(uuid.uuid4()), "title": f"{kpi_type.title()} {col}", "value": val, "type": kpi_type, "column": col, "format": fmt})
            
        return kpis

    @staticmethod
    def _generate_charts(df: pl.DataFrame, classifications: Dict[str, str]) -> List[Dict[str, Any]]:
        charts = []
        numeric_cols = [c for c, t in classifications.items() if t == "Numeric"]
        cat_cols = [c for c, t in classifications.items() if t == "Categorical_LowCard"]
        high_cat_cols = [c for c, t in classifications.items() if t == "Categorical_HighCard"]
        date_cols = [c for c, t in classifications.items() if t == "Date"]
        geo_cols = [c for c, t in classifications.items() if t == "Geo"]
        
        # Category Only -> Donut / Pie
        for cat in cat_cols[:2]:
            counts = df.group_by(cat).agg(pl.count().alias("count")).sort("count", descending=True).limit(10)
            data = counts.to_dicts()
            data = [{k: (v if v is not None else 'Unknown') for k, v in d.items()} for d in data]
            if not data or sum((d["count"] if isinstance(d["count"], (int, float)) else 0) for d in data) == 0: continue
            
            chart_type = "donut" if len(data) <= 5 else "bar"
            charts.append({
                "id": str(uuid.uuid4()), "title": f"Distribution by {cat}", "type": chart_type,
                "x_axis": cat, "y_axis": "count", "data": data, "width": 6, "height": 300
            })
            
        # Numeric + Category -> Horizontal Bar
        if numeric_cols and cat_cols:
            cat = cat_cols[0]
            num = numeric_cols[0]
            agg_df = df.group_by(cat).agg(pl.col(num).sum().alias(num)).sort(num, descending=True).limit(15)
            data = agg_df.to_dicts()
            data = [{k: (v if v is not None else 'Unknown') for k, v in d.items()} for d in data]
            if data and sum((d[num] if isinstance(d[num], (int, float)) else 0) for d in data) != 0:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"Top {cat} by {num}", "type": "horizontal_bar",
                    "x_axis": num, "y_axis": cat, "data": data, "width": 6, "height": 300
                })
            
        # Numeric + Date -> Line / Area
        if date_cols and numeric_cols:
            date_col = date_cols[0]
            num = numeric_cols[0]
            try:
                agg_df = df.drop_nulls([date_col]).group_by(date_col).agg(pl.col(num).sum().alias(num)).sort(date_col)
                if agg_df.height > 50: agg_df = agg_df.tail(50)
                data = agg_df.to_dicts()
                if data and sum((d[num] if isinstance(d[num], (int, float)) else 0) for d in data) != 0:
                    charts.append({
                        "id": str(uuid.uuid4()), "title": f"{num} Trend over {date_col}", "type": "line",
                        "x_axis": date_col, "y_axis": num, "data": data, "width": 12, "height": 350
                    })
            except: pass
                
        # Two Numeric -> Scatter
        if len(numeric_cols) >= 2:
            num1, num2 = numeric_cols[0], numeric_cols[1]
            sample = df.select([num1, num2]).drop_nulls().sample(n=min(500, df.height))
            data = sample.to_dicts()
            if data:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"{num1} vs {num2}", "type": "scatter",
                    "x_axis": num1, "y_axis": num2, "data": data, "width": 6, "height": 300
                })
            
        # Numeric Distribution -> Histogram
        if numeric_cols:
            num = numeric_cols[0]
            sample = df.select([num]).drop_nulls().sample(n=min(1000, df.height))
            data = sample.to_dicts()
            if data:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"Distribution of {num}", "type": "histogram",
                    "x_axis": num, "y_axis": "count", "data": data, "width": 6, "height": 350
                })
            
        # Outliers -> Box Plot
        if numeric_cols and cat_cols:
            num = numeric_cols[0]
            cat = cat_cols[0]
            sample = df.select([cat, num]).drop_nulls().sample(n=min(1000, df.height))
            data = sample.to_dicts()
            data = [{k: (v if v is not None else 'Unknown') for k, v in d.items()} for d in data]
            if data:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"Outliers: {num} by {cat}", "type": "box",
                    "x_axis": cat, "y_axis": num, "data": data, "width": 6, "height": 400
                })

        # Many Categories -> Treemap (never pie)
        if high_cat_cols and numeric_cols:
            cat = high_cat_cols[0]
            num = numeric_cols[0]
            agg_df = df.group_by(cat).agg(pl.col(num).sum().alias(num)).sort(num, descending=True).limit(50)
            data = agg_df.to_dicts()
            data = [{k: (v if v is not None else 'Unknown') for k, v in d.items()} for d in data]
            if data and sum((d[num] if isinstance(d[num], (int, float)) else 0) for d in data) != 0:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"Composition of {num} by {cat}", "type": "treemap",
                    "x_axis": cat, "y_axis": num, "data": data, "width": 6, "height": 400
                })
            
        # Many numeric columns -> Heatmap
        if len(cat_cols) >= 2 and numeric_cols:
            cat1, cat2 = cat_cols[0], cat_cols[1]
            num = numeric_cols[0]
            agg_df = df.group_by([cat1, cat2]).agg(pl.col(num).sum().alias(num))
            data = agg_df.to_dicts()
            data = [{k: (v if v is not None else 'Unknown') for k, v in d.items()} for d in data]
            if data and sum((d[num] if isinstance(d[num], (int, float)) else 0) for d in data) != 0:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"{num} by {cat1} and {cat2} (Heatmap)", "type": "heatmap",
                    "x_axis": cat1, "y_axis": cat2, "value_col": num, "data": data, "width": 6, "height": 400
                })
                
        # Geo data -> Map
        if geo_cols and numeric_cols:
            geo = geo_cols[0]
            num = numeric_cols[0]
            agg_df = df.group_by(geo).agg(pl.col(num).sum().alias(num)).sort(num, descending=True).limit(100)
            data = agg_df.to_dicts()
            data = [{k: (v if v is not None else 'Unknown') for k, v in d.items()} for d in data]
            if data and sum(d[num] for d in data) != 0:
                charts.append({
                    "id": str(uuid.uuid4()), "title": f"{num} by Location ({geo})", "type": "horizontal_bar", # fallback to horiz bar for map if no map library
                    "x_axis": num, "y_axis": geo, "data": data, "width": 12, "height": 350
                })

        return charts

    @staticmethod
    def _generate_filters(df: pl.DataFrame, classifications: Dict[str, str]) -> List[Dict[str, Any]]:
        filters = []
        cat_cols = [c for c, t in classifications.items() if t == "Categorical_LowCard"]
        for col in cat_cols[:4]:
            unique_vals = df.get_column(col).drop_nulls().unique().to_list()
            # limit to top 50 options to avoid overwhelming UI
            unique_vals = unique_vals[:50] if len(unique_vals) > 50 else unique_vals
            filters.append({
                "column": col,
                "type": "categorical",
                "label": f"Filter by {col}",
                "options": sorted([str(x) for x in unique_vals])
            })
            
        date_cols = [c for c, t in classifications.items() if t == "Date"]
        for col in date_cols[:1]:
             filters.append({
                "column": col,
                "type": "date_range",
                "label": f"Filter by {col}"
            })
            
        num_cols = [c for c, t in classifications.items() if t == "Numeric"]
        for col in num_cols[:2]:
             min_val = df.get_column(col).min()
             max_val = df.get_column(col).max()
             if min_val is not None and max_val is not None:
                 filters.append({
                    "column": col,
                    "type": "range",
                    "label": f"Range: {col}",
                    "min": min_val,
                    "max": max_val
                })
            
        return filters

    @staticmethod
    def _generate_insights(df: pl.DataFrame, charts: List[Dict[str, Any]]) -> List[str]:
        insights = []
        insights.append(f"Analyzed {df.height:,} records with {df.width} attributes.")
        
        # Missing values
        null_counts = df.null_count().to_dicts()[0]
        total_missing = sum(null_counts.values())
        if total_missing > 0:
            insights.append(f"Found **{total_missing:,} missing values** across the dataset which may impact analysis.")
        else:
            insights.append(f"Dataset is **100% clean** with no missing values.")
            
        try:
            duplicate_count = df.height - df.unique().height
            if duplicate_count > 0:
                insights.append(f"Identified **{duplicate_count:,} duplicate records** that could skew metrics.")
            else:
                insights.append(f"No duplicate records found, ensuring unique data integrity.")
        except: pass
        
        # Extrapolate insights from generated charts
        for chart in charts:
            if chart["type"] == "horizontal_bar":
                data = chart["data"]
                if data:
                    top_item = data[0]
                    cat = chart["y_axis"]
                    num = chart["x_axis"]
                    top_val = top_item.get(num, 0)
                    if isinstance(top_val, (int, float)):
                        insights.append(f"**{top_item.get(cat)}** has the highest '{num}' at {top_val:,}.")

        # Anomaly detection for numeric columns
        numeric_cols = [c for c, t in PowerBIDashboardEngine._classify_columns(df).items() if t == "Numeric"]
        for num in numeric_cols[:3]:
            try:
                s = df.get_column(num).drop_nulls()
                if len(s) > 10:
                    mean = s.mean()
                    std = s.std()
                    if std and std > 0:
                        outliers = s.filter(s > mean + 3 * std)
                        if len(outliers) > 0:
                            insights.append(f"Detected **{len(outliers)} anomalies** in '{num}' (values significantly above average).")
            except:
                pass
                
        # Correlations (simple heuristic)
        if len(numeric_cols) >= 2:
            try:
                num1, num2 = numeric_cols[0], numeric_cols[1]
                pearson_corr = df.select([pl.corr(num1, num2)]).item()
                if pearson_corr is not None:
                    if pearson_corr > 0.7:
                        insights.append(f"Strong **positive correlation** ({pearson_corr:.2f}) between '{num1}' and '{num2}'.")
                    elif pearson_corr < -0.7:
                        insights.append(f"Strong **negative correlation** ({pearson_corr:.2f}) between '{num1}' and '{num2}'.")
            except:
                pass
                    
        return insights

    @staticmethod
    def generate(df: pl.DataFrame, dataset_name: str = "Dataset") -> Dict[str, Any]:
        classifications = PowerBIDashboardEngine._classify_columns(df)
        
        kpis = PowerBIDashboardEngine._generate_kpis(df, classifications)
        charts = PowerBIDashboardEngine._generate_charts(df, classifications)
        filters = PowerBIDashboardEngine._generate_filters(df, classifications)
        insights = PowerBIDashboardEngine._generate_insights(df, charts)
        
        # Summary data
        numeric_count = len([c for c, t in classifications.items() if t == "Numeric"])
        cat_count = len([c for c, t in classifications.items() if "Categorical" in t])
        date_count = len([c for c, t in classifications.items() if t == "Date"])
        
        try:
            from app.services.data_quality import DataQualityService
            quality = DataQualityService.analyze_quality(df).get("scores", {}).get("overall_cleanliness", 100.0)
        except:
            quality = 95.0
            
        # Sample raw data for bottom table
        sample_data = df.head(100).to_dicts()
        import math
        for row in sample_data:
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    row[k] = None
        
        return {
            "title": f"{dataset_name} BI Dashboard",
            "summary": {
                "rows": df.height,
                "cols": df.width,
                "numeric": numeric_count,
                "categories": cat_count,
                "date_cols": date_count,
                "quality": quality
            },
            "kpis": kpis,
            "charts": charts,
            "filters": filters,
            "insights": insights,
            "sample_data": sample_data,
            "theme": {
                "primary": "#6366f1",
                "success": "#22c55e",
                "warning": "#f59e0b",
                "danger": "#ef4444"
            },
            "columns": classifications
        }

    @staticmethod
    def apply_filters(df: pl.DataFrame, active_filters: Dict[str, Any], dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        filtered_df = df
        
        for col, filter_val in active_filters.items():
            if col not in df.columns: continue
            
            if isinstance(filter_val, list):
                if filter_val:
                    filtered_df = filtered_df.filter(pl.col(col).is_in(filter_val))
            elif isinstance(filter_val, dict):
                min_val = filter_val.get("min")
                max_val = filter_val.get("max")
                if min_val is not None:
                    filtered_df = filtered_df.filter(pl.col(col) >= min_val)
                if max_val is not None:
                    filtered_df = filtered_df.filter(pl.col(col) <= max_val)

        classifications = dashboard_config.get("columns", {})
        new_kpis = PowerBIDashboardEngine._generate_kpis(filtered_df, classifications)
        new_charts = PowerBIDashboardEngine._generate_charts(filtered_df, classifications)
        
        new_config = dashboard_config.copy()
        new_config["kpis"] = new_kpis
        new_config["charts"] = new_charts
        
        return new_config
