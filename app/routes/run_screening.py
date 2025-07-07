from flask import Blueprint, render_template, request
from datetime import datetime
import pytz
import pandas as pd
from db import get_connection
from backend_screener import run_screener

bp = Blueprint('run_screening', __name__, url_prefix='/run-screening')

@bp.route('/', methods=['GET', 'POST'])
def run_screening():
    conn = get_connection()
    cursor = conn.cursor()

    message = None

    if request.method == 'POST':
        try:
            run_screener()
            message = "Screening berhasil dijalankan."
        except Exception as e:
            message = f"Terjadi error: {str(e)}"

    # Ambil data screening dari tanggal terakhir (MAX)
    cursor.execute("""
        SELECT 
            id, ticker, tanggal, harga, ema8, ema20, ema50, rsi,
            volume, avg_volume, status_rekomendasi, prioritas,
            created_at 
        FROM ScreeningResults
        WHERE tanggal = (SELECT MAX(tanggal) FROM ScreeningResults)
        ORDER BY prioritas ASC
    """)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    df = pd.DataFrame.from_records(rows, columns=columns) if rows else None

    cursor.close()
    conn.close()

    return render_template("run_screening.html",
                           message=message,
                           df=df,
                           show_button=True)  # tombol selalu tampil
