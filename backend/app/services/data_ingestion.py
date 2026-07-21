import polars as pl
import io

class DataIngestionService:
    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> dict:
        custom_na_values = [
            '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan',
            '1.#IND', '1.#QNAN', '<NA>', 'N/A', 'NA', 'NULL', 'NaN', 'n/a', 'nan', 'null'
        ]

        if filename.endswith(".csv"):
            try:
                df = pl.read_csv(file_content, infer_schema_length=0, ignore_errors=True)
                return {"Dataset": df}
            except Exception as e:
                try:
                    df = pl.read_csv(file_content, encoding='utf8-lossy', infer_schema_length=0)
                    return {"Dataset": df}
                except Exception as ex:
                    raise ValueError(f"CSV Parsing Error: {str(ex)}")
        elif filename.endswith(".tsv"):
            try:
                df = pl.read_csv(file_content, separator="\t", infer_schema_length=0, ignore_errors=True)
                return {"Dataset": df}
            except Exception as e:
                try:
                    df = pl.read_csv(file_content, separator="\t", encoding='utf8-lossy', infer_schema_length=0)
                    return {"Dataset": df}
                except Exception as ex:
                    raise ValueError(f"TSV Parsing Error: {str(ex)}")
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            try:
                import pandas as pd
                # sheet_name=None reads all sheets into a dict of pandas DataFrames
                dfs_dict = pd.read_excel(io.BytesIO(file_content), sheet_name=None, dtype=str, keep_default_na=False)
                result = {}
                for sheet_name, pdf in dfs_dict.items():
                    result[sheet_name] = pl.from_pandas(pdf)
                if not result:
                    raise ValueError("No sheets found in Excel file")
                return result
            except Exception as ex:
                raise ValueError(f"Excel Parsing Error: {str(ex)}")
        elif filename.endswith(".json"):
            try:
                df = pl.read_json(io.BytesIO(file_content), infer_schema_length=0)
                return {"Dataset": df}
            except Exception as e:
                raise ValueError(f"JSON Parsing Error: {str(e)}")
        else:
            raise ValueError("Unsupported file format")

    @staticmethod
    def get_overview(df: pl.DataFrame, filename: str, file_size: int) -> dict:
        num_rows, num_columns = df.shape
        columns = df.columns
        dtypes = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
        
        numerical_columns = [col for col, dtype in zip(df.columns, df.dtypes) if dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]]
        categorical_columns = [col for col, dtype in zip(df.columns, df.dtypes) if dtype in [pl.Utf8, pl.Categorical]]
        date_columns = [col for col, dtype in zip(df.columns, df.dtypes) if dtype in [pl.Datetime, pl.Date]]
        boolean_columns = [col for col, dtype in zip(df.columns, df.dtypes) if dtype == pl.Boolean]

        return {
            "filename": filename,
            "file_size_bytes": file_size,
            "num_rows": num_rows,
            "num_columns": num_columns,
            "columns": columns,
            "dtypes": dtypes,
            "numerical_columns": numerical_columns,
            "categorical_columns": categorical_columns,
            "date_columns": date_columns,
            "boolean_columns": boolean_columns
        }
