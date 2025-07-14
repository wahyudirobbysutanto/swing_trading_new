from flask import Blueprint, render_template, request, redirect, url_for
import pandas as pd
from db import get_connection
from backend_screener_new import recompute_status_from_watchlist_input

bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')

@bp.route('/', methods=['GET', 'POST'])
def watchlist():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Ambil ID dan nilai-nilai yang diubah dari form
        watchlist_id = request.form.get('id')
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

        # Konversi ke float jika bisa
        for k, v in update_fields.items():
            try:
                update_fields[k] = float(v) if v else None
            except:
                update_fields[k] = None

        # Update ke database
        cursor.execute("""
            UPDATE WatchlistPersonal_New
            SET harga=?, ema8=?, ema20=?, ema50=?, rsi=?,
                volume=?, avg_volume=?,
                ema8_weekly=?, ema20_weekly=?, ema50_weekly=?, rsi_weekly=?,
                manual_override=1
            WHERE id=?
        """, (
            update_fields['harga'], update_fields['ema8'], update_fields['ema20'], update_fields['ema50'],
            update_fields['rsi'],
            int(update_fields['volume']) if update_fields['volume'] else None,
            int(update_fields['avg_volume']) if update_fields['avg_volume'] else None,
            update_fields['ema8_weekly'], update_fields['ema20_weekly'],
            update_fields['ema50_weekly'], update_fields['rsi_weekly'],
            watchlist_id
        ))
        conn.commit()

        # Hitung ulang status dan update ke DB
        status, prio, entry_type, trend_pendek, harga_vs_ema, weekly_valid = recompute_status_from_watchlist_input(
            ticker=request.form.get('ticker'),
            tanggal=request.form.get('tanggal'),
            updated_fields=update_fields
        )

        cursor.execute("""
            UPDATE WatchlistPersonal_New
            SET status_rekomendasi=?, prioritas=?, entry_type=?,
                trend_pendek=?, harga_vs_ema=?, weekly_valid=?
            WHERE id=?
        """, (
            status, prio, entry_type, trend_pendek, harga_vs_ema, str(weekly_valid),
            watchlist_id
        ))
        conn.commit()

        return redirect(url_for('watchlist.watchlist'))

    # ========== GET Mode ==========
    # Ambil daftar tanggal
    cursor.execute("SELECT DISTINCT tanggal FROM WatchlistPersonal_New ORDER BY tanggal DESC")
    tanggal_rows = cursor.fetchall()
    tanggal_list = [str(row[0]) for row in tanggal_rows]

    # Tanggal yang sedang dipilih
    tanggal_aktif = request.args.get('tanggal') or tanggal_list[0]

    # Ambil data watchlist untuk tanggal aktif
    df = pd.read_sql("""
        SELECT * FROM WatchlistPersonal_New
        WHERE tanggal = ?
        ORDER BY prioritas ASC
    """, conn, params=[tanggal_aktif])

    editable_columns = [
        "harga", "ema8", "ema20", "ema50", "rsi",
        "volume", "avg_volume",
        "ema8_weekly", "ema20_weekly", "ema50_weekly", "rsi_weekly"
    ]

    cursor.close()
    conn.close()

    return render_template("watchlist.html",
                           df=df,
                           editable_columns=editable_columns,
                           tanggal_list=tanggal_list,
                           tanggal_aktif=tanggal_aktif)
