import pandas as pd
import io

class DataIngestionService:
    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> pd.DataFrame:
        # We explicitly omit the empty string ("") from the default NA values so that
        # truly empty cells are preserved as empty strings rather than converted to NaN.
        custom_na_values = [
            '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan',
            '1.#IND', '1.#QNAN', '<NA>', 'N/A', 'NA', 'NULL', 'NaN', 'n/a', 'nan', 'null'
        ]

        if filename.endswith(".csv"):
            try:
                return pd.read_csv(io.BytesIO(file_content), keep_default_na=False, na_values=custom_na_values)
            except UnicodeDecodeError:
                return pd.read_csv(io.BytesIO(file_content), encoding='latin-1', keep_default_na=False, na_values=custom_na_values)
            except Exception as e:
                raise ValueError(f"CSV Parsing Error: {str(e)}")
        elif filename.endswith(".tsv"):
            try:
                return pd.read_csv(io.BytesIO(file_content), sep="\t", keep_default_na=False, na_values=custom_na_values)
            except UnicodeDecodeError:
                return pd.read_csv(io.BytesIO(file_content), sep="\t", encoding='latin-1', keep_default_na=False, na_values=custom_na_values)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            try:
                return pd.read_excel(io.BytesIO(file_content), keep_default_na=False, na_values=custom_na_values)
            except Exception as e:
                raise ValueError(f"Excel Parsing Error: {str(e)}")
        elif filename.endswith(".json"):
            try:
                return pd.read_json(io.BytesIO(file_content))
            except Exception as e:
                raise ValueError(f"JSON Parsing Error: {str(e)}")
        else:
            raise ValueError("Unsupported file format")

    @staticmethod
    def get_overview(df: pd.DataFrame, filename: str, file_size: int) -> dict:
        num_rows, num_columns = df.shape
        columns = df.columns.tolist()
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        numerical_columns = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
        date_columns = df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
        boolean_columns = df.select_dtypes(include=['bool']).columns.tolist()

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
