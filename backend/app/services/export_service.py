import pandas as pd
import io

class ExportService:
    @staticmethod
    def export_csv(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode('utf-8')
        
    @staticmethod
    def export_html(df: pd.DataFrame, quality_report: dict) -> bytes:
        metrics = quality_report.get('metrics', {})
        scores = quality_report.get('scores', {})
        anomalies = quality_report.get('anomalies', {})
        
        # Build Column Duplicates Table
        col_dups_html = ""
        if anomalies.get("col_duplicates_details"):
            col_dups_html += "<h3>Column-Level Duplicate Values</h3><table class='table table-bordered'><tr><th>Column Name</th><th>Duplicate Value</th><th>Appears In Rows</th></tr>"
            for dup in anomalies["col_duplicates_details"]:
                rows_str = ", ".join(map(str, dup['rows']))
                if dup['has_more']:
                    rows_str += f" ...and {dup['total_appearances'] - len(dup['rows'])} more"
                col_dups_html += f"<tr><td>{dup['column']}</td><td>{dup['value']}</td><td>{rows_str}</td></tr>"
            col_dups_html += "</table>"
            
        # Build Row Duplicates Table
        row_dups_html = ""
        if anomalies.get("row_duplicates_details"):
            row_dups_html += "<h3>Exact Row-Level Duplicates</h3><table class='table table-bordered'><tr><th>Original Row</th><th>Duplicate Rows</th></tr>"
            for dup in anomalies["row_duplicates_details"]:
                rows_str = ", ".join(map(str, dup['duplicate_rows']))
                if dup['has_more']:
                    rows_str += f" ...and {dup['total_duplicates'] - len(dup['duplicate_rows'])} more"
                row_dups_html += f"<tr><td>Row {dup['original_row']}</td><td>{rows_str}</td></tr>"
            row_dups_html += "</table>"
            
        html = f"""
        <html>
        <head>
            <title>Data Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; color: #333; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th, td {{ border: 1px solid #bdc3c7; padding: 8px; text-align: left; }}
                th {{ background-color: #ecf0f1; }}
                .summary-list li {{ margin-bottom: 8px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Enterprise Data Analysis Report</h1>
            
            <h2>Data Quality Summary</h2>
            <ul class="summary-list">
                <li>Overall Cleanliness Score: {scores.get('overall_cleanliness', 0)}%</li>
                <li>Total Missing Values: {metrics.get('total_missing_values', 0)}</li>
                <li>Total Empty Cells: {metrics.get('total_empty_cells', 0)}</li>
                <li>Total Exact Duplicate Rows: {metrics.get('total_exact_duplicates', 0)}</li>
                <li>Total Outliers: {metrics.get('total_outliers', 0)}</li>
            </ul>
            
            <h2>Duplicate Summary</h2>
            <p>Total Duplicate Rows: {metrics.get('total_exact_duplicates', 0)}</p>
            <p>Columns Containing Duplicates: {anomalies.get('columns_containing_duplicates', 0)}</p>
            
            {row_dups_html}
            {col_dups_html}
            
            <h2>Data Preview (Top 100 rows)</h2>
            {df.head(100).to_html(classes="table table-striped", index=False)}
        </body>
        </html>
        """
        return html.encode('utf-8')
