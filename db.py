import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    server = os.getenv("SQL_SERVER")
    database = os.getenv("SQL_DATABASE")
    use_windows_auth = os.getenv("USE_WINDOWS_AUTH", "false").lower() == "true"

    if use_windows_auth:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};Trusted_Connection=yes;"
        )
    else:
        user = os.getenv("SQL_USER")
        password = os.getenv("SQL_PASSWORD")
        if not user or not password:
            raise ValueError("SQL_USER dan SQL_PASSWORD harus diatur di .env jika tidak menggunakan Windows Authentication.")
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={user};PWD={password};"
        )

    return pyodbc.connect(conn_str)
