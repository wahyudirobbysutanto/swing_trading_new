from flask import Blueprint, render_template, request, redirect, url_for
import pandas as pd
from db import get_connection
from backend_screener import evaluate_recommendation, generate_additional_insight  # pastikan fungsi ini tersedia

bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')

@bp.route('/', methods=['GET', 'POST'])
def watchlist():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        watchlist_id = request.form.get('id')
        
        # Ambil nilai-nilai baru
        update_fields = {
            'harga': request.form.get('harga'),
            'ema8': request.form.get('ema8'),
            'ema20': request.form.get('ema20'),
            'ema50': request.form.get('ema50'),
            'rsi': request.form.get('rsi'),
            'volume': request.form.get('volume'),
            'avg_volume': request.form.get('avg_volume'),
            'ema8_weekly': request.form.get('ema8_weekly'),
            'ema20_weekly': request.form.get('ema20_weekly'),
            'ema50_weekly': request.form.get('ema50_weekly'),
            'rsi_weekly': request.form.get('rsi_weekly'),
        }

        # Cast ke float atau None
        for k, v in update_fields.items():
            try:
                update_fields[k] = float(v) if v else None
            except:
                update_fields[k] = None

        # Hitung status_rekomendasi baru
        status, prio, entry_type = evaluate_recommendation(
            harga=update_fields['harga'],
            ema8=update_fields['ema8'],
            ema20=update_fields['ema20'],
            ema50=update_fields['ema50'],
            rsi=update_fields['rsi'],
            volume=update_fields['volume'],
            avg_volume=update_fields['avg_volume'],
            prev_ema8=None,
            prev_ema20=None,
            prev_ema50=None,
            prev_rsi=None,
            prev_volume=None,
            prev_avg_volume=None
        )

        # print(ticker)
        trend_pendek, harga_vs_ema, weekly_valid = generate_additional_insight (
            ticker=request.form.get('ticker'), 
            harga=update_fields['harga'], 
            ema8=update_fields['ema8'], 
            ema20=update_fields['ema20'], 
            ema50=update_fields['ema50'],
            ema8_weekly=update_fields['ema8_weekly'], 
            ema20_weekly=update_fields['ema20_weekly'], 
            ema50_weekly=update_fields['ema50_weekly']
        )

        # print(trend_pendek)
        # print(harga_vs_ema)
        # print(weekly_valid)

        print(update_fields['ema8'])
        print(update_fields['ema20'])
        print(update_fields['ema50'])
        print(update_fields['rsi'])
        print(update_fields['volume'])
        print(update_fields['avg_volume'])
        print(update_fields['ema8_weekly'])
        print(update_fields['ema20_weekly'])
        print(update_fields['rsi_weekly'])

        # Update ke DB
        cursor.execute("""
            UPDATE WatchlistPersonal
            SET harga=?, ema8=?, ema20=?, ema50=?, rsi=?,
                volume=?, avg_volume=?,
                ema8_weekly=?, ema20_weekly=?, ema50_weekly=?, rsi_weekly=?,
                status_rekomendasi=?, prioritas=?, manual_override=1, trend_pendek=?, harga_vs_ema=?, weekly_valid=?
            WHERE id=?
        """, (
            update_fields['harga'],
            update_fields['ema8'],
            update_fields['ema20'],
            update_fields['ema50'],
            update_fields['rsi'],
            int(update_fields['volume']) if update_fields['volume'] else None,
            int(update_fields['avg_volume']) if update_fields['avg_volume'] else None,
            update_fields['ema8_weekly'],
            update_fields['ema20_weekly'],
            update_fields['ema50_weekly'],
            update_fields['rsi_weekly'],
            status, prio, trend_pendek, harga_vs_ema, weekly_valid,
            watchlist_id
        ))
        conn.commit()

        return redirect(url_for('watchlist.watchlist'))

    # Ambil semua data
    df = pd.read_sql("""SELECT * FROM WatchlistPersonal 
    WHERE tanggal = (SELECT MAX(tanggal) FROM WatchlistPersonal)
    ORDER BY tanggal DESC""", conn)
    rows = df.to_dict(orient='records')
    columns = df.columns.tolist()

    cursor.close()
    conn.close()

    editable_columns = [
        "harga", "ema8", "ema20", "ema50", "rsi",
        "volume", "avg_volume",
        "ema8_weekly", "ema20_weekly", "ema50_weekly", "rsi_weekly"
    ]
    return render_template("watchlist.html", df=df, editable_columns=editable_columns)

    # return render_template("watchlist.html", rows=rows, columns=columns)
