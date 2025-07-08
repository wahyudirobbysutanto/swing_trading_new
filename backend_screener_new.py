import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from db import get_connection
from utils import get_idx_tickers_from_excel


# ==========================
# Indicator Calculation
# ==========================

def calculate_ema(series, period):
    ema = series.copy()
    sma = series.rolling(window=period).mean()
    multiplier = 2 / (period + 1)
    for i in range(len(series)):
        if i < period:
            ema.iloc[i] = np.nan
        elif i == period:
            ema.iloc[i] = sma.iloc[i]
        else:
            ema.iloc[i] = (series.iloc[i] - ema.iloc[i - 1]) * multiplier + ema.iloc[i - 1]
    return ema

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rsi = pd.Series(index=series.index, dtype='float64')
    for i in range(len(series)):
        if i < period:
            rsi.iloc[i] = np.nan
        else:
            prev_gain = avg_gain.iloc[i]
            prev_loss = avg_loss.iloc[i]
            rs = prev_gain / prev_loss if prev_loss != 0 else 0
            rsi.iloc[i] = 100 - (100 / (1 + rs))
    return rsi

def calculate_indicators(df):
    df['EMA8'] = calculate_ema(df['Close'], 8)
    df['EMA20'] = calculate_ema(df['Close'], 20)
    df['EMA50'] = calculate_ema(df['Close'], 50)
    df['RSI'] = compute_rsi(df['Close'], 14)
    df['AvgVolume10'] = df['Volume'].rolling(window=10).mean()
    return df.dropna()

def generate_additional_insight_from_sql(closes_3days, harga, ema8, ema20, ema50,
                                         ema8_weekly, ema20_weekly, ema50_weekly):
    trend_pendek = "unknown"
    harga_vs_ema = "unknown"
    weekly_valid = False

    try:
        # Cek trend 3 hari terakhir (dari close price harian)
        if len(closes_3days) >= 3:
            if closes_3days[-1] > closes_3days[-2] > closes_3days[-3]:
                trend_pendek = "naik"
            elif closes_3days[-1] < closes_3days[-2] < closes_3days[-3]:
                trend_pendek = "turun"
            else:
                trend_pendek = "netral"

        # Posisi harga terhadap EMA
        if harga > ema8 and harga > ema20:
            harga_vs_ema = "di atas semua"
        elif harga > ema20:
            harga_vs_ema = "di atas EMA20"
        elif harga > ema8:
            harga_vs_ema = "di atas EMA8"
        else:
            harga_vs_ema = "di bawah EMA"

        # Validasi trend mingguan
        if all(x not in [None, 0] for x in [ema8_weekly, ema20_weekly, ema50_weekly]):
            if ema8_weekly > ema20_weekly and harga > ema50_weekly:
                weekly_valid = True


    except Exception as e:
        print(f"[generate_additional_insight_from_sql] Error: {e}")

    return trend_pendek, harga_vs_ema, weekly_valid


# ==========================
# Screening Helpers
# ==========================

def is_bearish_engulfing(df):
    if df is None or df.empty or len(df) < 2:
        return False
    df = df.dropna()
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    return (
        float(prev['Close']) > float(prev['Open']) and
        float(curr['Close']) < float(curr['Open']) and
        float(curr['Open']) > float(prev['Close']) and
        float(curr['Close']) < float(prev['Open'])
    )

def is_breaking_10_day_high(df):
    if df is None or df.empty or len(df) < 11:
        return False
    last_close = df['Close'].iloc[-1]
    past_10_high = df['High'].iloc[-11:-1].max()
    return float(last_close) > float(past_10_high)

def is_rsi_dropping(df):
    return len(df) >= 3 and df['RSI'].iloc[-1] < df['RSI'].iloc[-2]

def is_volume_dropping(df):
    return len(df) >= 3 and df['Volume'].iloc[-1] < df['Volume'].iloc[-2]

def is_valid_breakout(df):
    if len(df) < 12:
        return False
    last_5_range = df['Close'].iloc[-6:-1].max() - df['Close'].iloc[-6:-1].min()
    today_close = df['Close'].iloc[-1]
    avg_volume = df['Volume'].iloc[-11:-1].mean()
    today_volume = df['Volume'].iloc[-1]
    breakout_ok = last_5_range < 0.03 * today_close
    volume_ok = today_volume > 1.2 * avg_volume
    return breakout_ok and volume_ok


def get_entry_type_status_priority(latest, prev, weekly_valid=False):
    close = float(latest['Close'])
    ema8 = float(latest['EMA8'])
    ema20 = float(latest['EMA20'])
    ema50 = float(latest['EMA50'])
    rsi = float(latest['RSI'])
    volume = float(latest['Volume'])
    avg_vol = float(latest['AvgVolume10'])
    cross_today = ema8 > ema20
    cross_yesterday = float(prev['EMA8']) < float(prev['EMA20'])
    momentum = float(prev['EMA8']) > float(prev['EMA20'])
    volume_ok = volume > 0.8 * avg_vol

    entry_type = "no_entry"

    if close > ema50 and cross_today and cross_yesterday and rsi >= 70 and volume > avg_vol:
        entry_type = "breakout_today"
        status = "yes-agresif"
        priority = 1
    elif close > ema50 and cross_today and not cross_yesterday and 50 < rsi < 70 and volume_ok:
        entry_type = "pullback_entry"
        status = "yes"
        priority = 2
    elif close > ema50 and cross_today and (cross_yesterday or momentum) and rsi >= 70:
        entry_type = "momentum_entry"
        status = "yes-agresif"
        priority = 3
    elif close > ema50 and cross_today and (cross_yesterday or momentum) and 50 < rsi < 70 and volume_ok:
        entry_type = "momentum_entry"
        status = "yes"
        priority = 4
    elif close > ema50 and cross_today and (cross_yesterday or momentum) and volume < avg_vol:
        entry_type = "volume_weak"
        status = "yes-volume-kurang"
        priority = 5
    else:
        entry_type = "no_entry"
        status = "no"
        priority = 9

    # Modifikasi jika weekly valid
    if weekly_valid:
        if priority > 1:
            priority -= 1
        if status.startswith("yes"):
            status += "-weekly"

    return entry_type, status, priority




# ==========================
# Main Screener Function
# ==========================

def run_screener_new():
    conn = get_connection()
    cursor = conn.cursor()
    tickers = get_idx_tickers_from_excel('data/Stock_List.xlsx')
    wib_now = datetime.now(pytz.timezone("Asia/Jakarta"))
    skip_today = wib_now.hour < 15

    # tickers = ['YUPI.JK']

    for ticker in tickers:
        ticker_clean = ticker.replace(".JK", "")
        df = pd.read_sql("""
            SELECT tanggal, open_price AS [Open], high_price AS [High],
                   low_price AS [Low], close_price AS [Close], volume AS [Volume]
            FROM DailyPrice
            WHERE ticker = ?
            ORDER BY tanggal ASC
        """, conn, params=[ticker_clean])

        if df.empty or len(df) < 30:
            continue

        df['Date'] = pd.to_datetime(df['tanggal'])
        df.set_index('Date', inplace=True)
        df = calculate_indicators(df)

        if skip_today:
            df = df.iloc[:-1]

        if len(df) < 3:
            continue

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        if len(df) >= 10:
            high10 = df['High'].rolling(window=10).max().iloc[-1]
            low10 = df['Low'].rolling(window=10).min().iloc[-1]
        else:
            high10 = 0  # atau np.nan jika kamu ingin tetap eksplisit
            low10 = 0


        # Weekly default (diisi 0)
        ema8w = ema20w = ema50w = rsiw = 0  # default jika weekly tidak tersedia

        if len(df) >= 60:
            # Ambil data mingguan dari harian (1 data/minggu, misalnya setiap Jumat)
            weekly_df = df.resample('W-FRI').last().dropna()

            if len(weekly_df) >= 20:  # pastikan cukup untuk EMA50
                weekly_df['EMA8W'] = calculate_ema(weekly_df['Close'], 8)
                weekly_df['EMA20W'] = calculate_ema(weekly_df['Close'], 20)
                weekly_df['EMA50W'] = calculate_ema(weekly_df['Close'], 50)
                weekly_df['RSIW'] = compute_rsi(weekly_df['Close'])

                latest_week = weekly_df.iloc[-1]
                ema8w = float(latest_week['EMA8W']) if not pd.isna(latest_week['EMA8W']) else 0
                ema20w = float(latest_week['EMA20W']) if not pd.isna(latest_week['EMA20W']) else 0
                ema50w = float(latest_week['EMA50W']) if not pd.isna(latest_week['EMA50W']) else 0
                rsiw = float(latest_week['RSIW']) if not pd.isna(latest_week['RSIW']) else 0


        # Data harian (yang diperlukan)
        harga = float(latest['Close'])
        ema8 = float(latest['EMA8'])
        ema20 = float(latest['EMA20'])
        ema50 = float(latest['EMA50'])

        closes_3days = df['Close'].tail(3).tolist()
        trend_pendek, harga_vs_ema, weekly_valid = generate_additional_insight_from_sql(
            closes_3days,
            harga, ema8, ema20, ema50,
            ema8w, ema20w, ema50w
        )

        breakout_ok = is_valid_breakout(df)
        reject = is_bearish_engulfing(df) or not is_breaking_10_day_high(df) or is_rsi_dropping(df) or is_volume_dropping(df)

        if breakout_ok and not reject:
            entry_type, status, priority = get_entry_type_status_priority(latest, prev, weekly_valid=weekly_valid)
        else:
            entry_type, status, priority = "rejected_filter", "not_recommended", 9

        print(ticker_clean)

        # Insert ke ScreeningResults_New dan ambil ID-nya
        cursor.execute("""
            INSERT INTO ScreeningResults_New (
                ticker, tanggal, harga, ema8, ema20, ema50, rsi, volume, avg_volume,
                prev_ema8, prev_ema20, prev_ema50, prev_rsi, prev_volume, prev_avg_volume,
                ema8_weekly, ema20_weekly, ema50_weekly, rsi_weekly,
                status_rekomendasi, prioritas, breakout_valid, entry_type, high10, low10
            ) OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker_clean, latest.name.date(),
            float(latest['Close']), float(latest['EMA8']), float(latest['EMA20']), float(latest['EMA50']),
            float(latest['RSI']), int(latest['Volume']), int(latest['AvgVolume10']),
            float(prev['EMA8']), float(prev['EMA20']), float(prev['EMA50']),
            float(prev['RSI']), int(prev['Volume']), int(prev['AvgVolume10']),
            ema8w, ema20w, ema50w, rsiw,
            status, priority, int(breakout_ok), entry_type,
            float(high10), float(low10)
        ))

        print('x')
        screening_id = cursor.fetchone()[0]

        # Auto insert ke Watchlist jika prioritas 1–2
        if priority in [1, 2]:
            cursor.execute("""
                INSERT INTO WatchlistPersonal_New (
                    ticker, tanggal, harga, ema8, ema20, ema50, rsi, volume, avg_volume,
                    prev_ema8, prev_ema20, prev_ema50, prev_rsi, prev_volume, prev_avg_volume,
                    ema8_weekly, ema20_weekly, ema50_weekly, rsi_weekly,
                    high10, low10, status_rekomendasi, prioritas,
                    source_screening_id, manual_override, trend_pendek, harga_vs_ema, weekly_valid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker_clean, latest.name.date(), float(latest['Close']), float(latest['EMA8']), float(latest['EMA20']), float(latest['EMA50']), float(latest['RSI']), int(latest['Volume']), int(latest['AvgVolume10']),
                float(prev['EMA8']), float(prev['EMA20']), float(prev['EMA50']), float(prev['RSI']), int(prev['Volume']), int(prev['AvgVolume10']),
                ema8w, ema20w, ema50w, rsiw,
                float(high10), float(low10), status, priority,
                screening_id, 0, trend_pendek, harga_vs_ema, str(weekly_valid)
            ))

        conn.commit()

    cursor.close()
    conn.close()
    print("Screening selesai.")


if __name__ == "__main__":
    run_screener_new()
