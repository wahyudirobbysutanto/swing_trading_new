from flask import Blueprint, render_template
import pandas as pd
import sys
import os
from db import get_connection


bp = Blueprint('dashboard', __name__)

@bp.route('/')
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    df = pd.read_sql("""
        SELECT tanggal, ticker, harga, status_rekomendasi, prioritas
        FROM ScreeningResults
        WHERE tanggal = (SELECT MAX(tanggal) FROM ScreeningResults)
    """, conn)

    prioritas_counts = df['prioritas'].value_counts().sort_index().to_dict()
    closing_prices = df[df['prioritas'].isin([1, 2])].set_index('ticker')['harga'].to_dict()


    # penjelasan_prio_1 = (
    #     "Prioritas 1 berarti saham mengalami breakout hari ini dengan volume tinggi. "
    #     "Ini menunjukkan potensi naik cepat dan cocok untuk entry agresif."
    # )

    cursor.close()
    conn.close()

    return render_template("dashboard.html",
                       prioritas_counts=prioritas_counts,
                       closing_prices=closing_prices
                    #    ,penjelasan_prio_1=penjelasan_prio_1
                       )


