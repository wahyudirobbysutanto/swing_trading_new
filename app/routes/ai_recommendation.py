from flask import Blueprint, render_template, request, jsonify
from db import get_connection
from gemini_client import ask_gemini
import pandas as pd

bp = Blueprint("ai_recommendation", __name__, url_prefix="/ai-recommendation")

# Fungsi bantu: membentuk prompt dari data watchlist
def build_prompt_from_data(data):
    prompt = f"""
    Saya ingin Anda bertindak sebagai analis swing trading profesional.

    Gunakan hanya data teknikal berikut (jangan menggunakan data lain atau menyarankan untuk melihat chart):
    - Harga: {data['harga']}
    - EMA8: {data['ema8']}
    - EMA20: {data['ema20']}
    - EMA50: {data['ema50']}
    - RSI: {data['rsi']}
    - Volume: {data['volume']}
    - Avg Volume: {data['avg_volume']}
    - EMA8 Weekly: {data['ema8_weekly']}
    - EMA20 Weekly: {data['ema20_weekly']}
    - EMA50 Weekly: {data['ema50_weekly']}
    - RSI Weekly: {data['rsi_weekly']}

    📈 Informasi tambahan:
    - Trend pendek (3 hari terakhir): {data['trend_pendek']}
    - Posisi harga terhadap EMA: {data['harga_vs_ema']}
    - Validitas setup mingguan: {"Valid" if data['weekly_valid'] else "Tidak Valid"}


    Berdasarkan data tersebut, berikan rekomendasi swing trading untuk 1–5 hari ke depan dengan format berikut:

    1. Rekomendasi: [Layak / Tidak Layak]
    2. Entry Price: [angka]
    3. Target Profit (TP): [angka]
    4. Cut Loss (CL): [angka]
    5. Penjelasan: [maksimal 2 kalimat, teknikal, tegas]
    """

    # prompt = f"""
    # Saya ingin kamu bertindak sebagai analis teknikal saham profesional untuk swing trading berbasis strategi EMA crossover.
    

    # 📊 Data teknikal harian saham {data['ticker']} per {data['tanggal']}:
    # - Close: {data['harga']}
    # - EMA8: {data['ema8']}
    # - EMA20: {data['ema20']}
    # - EMA50: {data['ema50']}
    # - RSI: {data['rsi']}
    # - Volume: {data['volume']}
    # - Avg Volume 10d: {data['avg_volume']}
    # - Status Screening: {data['status_rekomendasi']}

    # 📈 Data teknikal mingguan:
    # - EMA8 Weekly: {data['ema8_weekly']}
    # - EMA20 Weekly: {data['ema20_weekly']}
    # - EMA50 Weekly: {data['ema50_weekly']}
    # - RSI Weekly: {data['rsi_weekly']}

    # 📘 Strategi Swing Trading (yang harus kamu ikuti):
    # 1. Entry jika EMA8 > EMA20 dan Harga > EMA50 (baik di daily dan weekly)
    # 2. Volume harus lebih tinggi dari rata-rata
    # 3. RSI ideal antara 55–75; RSI > 80 dianggap overbought
    # 4. EMA8 Weekly < EMA20 Weekly = Tidak layak entry
    # 5. TP = resistance terdekat, CL = support terdekat atau breakdown EMA20
    # 6. Rasio risk:reward minimal 1:2

    # 📌 Tugas kamu:
    # - Evaluasi apakah saham ini layak untuk swing entry (1–5 hari ke depan)
    # - Jika layak, berikan angka pasti: Entry Price, TP, dan CL
    # - Jawaban harus berdasarkan data di atas saja
    # - Jangan menyarankan untuk melihat chart atau informasi tambahan
    # - Jawab dengan format berikut dan jangan ubah strukturnya:

    # Format Jawaban:
    # 1. Validitas Setup: [Valid / Tidak Valid]
    # 2. Rekomendasi: [Layak / Tidak Layak]
    # 3. Entry Price: [angka]
    # 4. Take Profit: [angka]
    # 5. Cut Loss: [angka]
    # 6. Alasan Singkat: [maks 2 kalimat teknikal]
    # """
    return prompt


@bp.route("/", methods=["GET", "POST"])
def ai_recommendation():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        ticker = request.form.get("ticker")
        if ticker:
            # Ambil data dari WatchlistPersonal untuk ticker ini
            cursor.execute("""
                SELECT * FROM WatchlistPersonal
                WHERE ticker = ? 
                AND tanggal = (SELECT MAX(tanggal) FROM WatchlistPersonal)
                ORDER BY tanggal DESC
            """, (ticker,))
            row = cursor.fetchone()
            if row:
                col_names = [desc[0] for desc in cursor.description]
                data = dict(zip(col_names, row))

                # Buat prompt dan panggil fungsi AI
                prompt = build_prompt_from_data(data)
                text = ask_gemini(prompt)
                if text:
                    # Misal kita ingin ambil rekomendasi dan penjelasan terpisah (jika dibatasi)
                    rekomendasi = "Layak" if "layak" in text.lower() else "Tidak Layak"
                    print(text)
                    ai_response = {
                        "rekomendasi": rekomendasi,
                        "penjelasan": text
                    }
                else:
                    ai_response = {
                        "rekomendasi": "Tidak Tersedia",
                        "penjelasan": "Gagal mengambil jawaban dari Gemini."
                    }

                # Simpan ke AIRecommendations
                cursor.execute("""
                    INSERT INTO AIRecommendations (ticker, tanggal, versi, rekomendasi, penjelasan, source_data, watchlist_id)
                    VALUES (?, ?, 'ai_own_data', ?, ?, ?, ?)
                """, (
                    data['ticker'],
                    data['tanggal'],
                    ai_response['rekomendasi'],
                    ai_response['penjelasan'],
                    str(prompt),
                    data['id']
                ))
                conn.commit()

    # Ambil semua dari WatchlistPersonal
    df = pd.read_sql("""
        SELECT * FROM WatchlistPersonal
        WHERE tanggal = (SELECT MAX(tanggal) FROM WatchlistPersonal)
        ORDER BY tanggal DESC
    """, conn)

    # Cek yang sudah punya AI recommendation
    cursor.execute("SELECT DISTINCT ticker FROM AIRecommendations")
    existing = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return render_template("ai_recommendation.html", df=df, existing_ai=existing)


@bp.route("/view")
def view_ai():
    ticker = request.args.get("ticker")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT versi, rekomendasi, penjelasan
        FROM AIRecommendations
        WHERE ticker = ?
        AND tanggal = (SELECT MAX(tanggal) FROM WatchlistPersonal)
        ORDER BY created_at DESC
    """, (ticker,))
    rows = cursor.fetchall()

    data = {"user": "", "ai": ""}
    for versi, rekom, penjelasan in rows:
        if versi == "user_data":
            data["user"] = f"{rekom}\n{penjelasan}"
        elif versi == "ai_own_data":
            data["ai"] = f"{rekom}\n{penjelasan}"

    cursor.close()
    conn.close()
    return jsonify(data)


# Fungsi
