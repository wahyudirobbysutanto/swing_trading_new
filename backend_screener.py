import yfinance as yf
import pandas as pd
import numpy as np
import pytz

from db import get_connection
from datetime import datetime
from utils import get_idx_tickers_from_excel


def evaluate_recommendation(harga, ema8, ema20, ema50, rsi, volume, avg_volume,
                            prev_ema8=None, prev_ema20=None, prev_ema50=None,
                            prev_rsi=None, prev_volume=None, prev_avg_volume=None):
    """
    Evaluasi status rekomendasi berdasarkan indikator teknikal yang diedit user di halaman watchlist.
    """
    status = "hold"
    priority = 9
    entry_type = "unknown"

    try:
        # Cek breakout dengan volume tinggi
        if harga > ema8 > ema20 > ema50 and rsi >= 65 and volume > avg_volume:
            status = "yes_breakout"
            priority = 1
            entry_type = "agresif"

        # Cek pullback sehat
        elif ema8 > ema20 > ema50 and rsi > 55 and volume >= avg_volume * 0.8 and harga > ema20:
            status = "yes_pullback"
            priority = 2
            entry_type = "moderate"

        # Cek tren naik lemah
        elif ema8 > ema20 > ema50 and rsi > 50:
            status = "watching_only"
            priority = 3
            entry_type = "weak"

        # Kondisi netral atau tidak layak entry
        else:
            status = "not_recommended"
            priority = 9
            entry_type = "none"
    except Exception as e:
        print(f"[evaluate_recommendation] error: {e}")

    return status, priority, entry_type


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
    rs = 0

    for i in range(len(series)):
        if i < period:
            rsi.iloc[i] = np.nan
        elif i == period:
            gain_val = avg_gain.iloc[i].item()
            loss_val = avg_loss.iloc[i].item()
            rsi.iloc[i] = 100 - (100 / (1 + rs))
            prev_gain = gain_val
            prev_loss = loss_val
            if prev_loss == 0:
                rs = 0
            else:
                rs = prev_gain / prev_loss
            # rs = 0 if loss_val == 0 else gain_val / loss_val
            
        else:
            gain_i = gain.iloc[i].item()
            loss_i = loss.iloc[i].item()
            prev_gain = (prev_gain * (period - 1) + gain_i) / period
            prev_loss = (prev_loss * (period - 1) + loss_i) / period
            
            if prev_loss == 0:
                rs = 0
            else:
                rs = prev_gain / prev_loss
            # rs = 0 if prev_loss == 0 else prev_gain / prev_loss
            rsi.iloc[i] = 100 - (100 / (1 + rs))

    return rsi

def calculate_indicators(df):
    df['EMA8'] = calculate_ema(df['Close'], 8)
    df['EMA20'] = calculate_ema(df['Close'], 20)
    df['EMA50'] = calculate_ema(df['Close'], 50)
    df['RSI'] = compute_rsi(df['Close'], 14)
    df['AvgVolume10'] = df['Volume'].rolling(window=10).mean()
    return df.dropna()


# ==========================
# Screening Logic
# ==========================

def is_valid_breakout(df):
    if len(df) < 12:
        return False

    # last_5_range = df['Close'].iloc[-6:-1].max() - df['Close'].iloc[-6:-1].min()
    last_5_closes = df['Close'].iloc[-6:-1]
    last_5_range = float(last_5_closes.max() - last_5_closes.min())

    today_close = float(df['Close'].iloc[-1])
    avg_volume = float(df['Volume'].iloc[-11:-1].mean())
    today_volume = float(df['Volume'].iloc[-1])

    breakout_range_ok = last_5_range < 0.03 * today_close
    volume_spike_ok = today_volume > 1.2 * avg_volume

    # print('--------------------')
    # print(breakout_range_ok)
    # print('--------------------')
    # print(volume_spike_ok)
    # print('--------------------')

    return breakout_range_ok and volume_spike_ok


def get_entry_type_status_priority(latest, prev):
    close = float(latest['Close'])
    ema8 = round(float(latest['EMA8']),2 )
    ema20 = round(float(latest['EMA20']), 2)
    ema50 = round(float(latest['EMA50']), 2)
    rsi = round(float(latest['RSI']), 2)

    volume = latest['Volume'].item() if isinstance(latest['Volume'], pd.Series) else float(latest['Volume'])
    avg_vol = latest['AvgVolume10'].item() if isinstance(latest['AvgVolume10'], pd.Series) else float(latest['AvgVolume10'])
    cross_today = ema8 > ema20
    cross_yesterday = round(float(prev['EMA8']), 2) < round(float(prev['EMA20']), 2)
    momentum = round(float(prev['EMA8']), 2) > round(float(prev['EMA20']), 2)
    volume_ok = volume > 0.8 * avg_vol

    if close > ema50 and cross_today and cross_yesterday and rsi >= 70 and volume > avg_vol:
        return "breakout_today", "yes-agresif", 1
    if close > ema50 and cross_today and not cross_yesterday and 50 < rsi < 70 and volume_ok:
        return "pullback_entry", "yes", 2
    if close > ema50 and cross_today and (cross_yesterday or momentum) and rsi >= 70:
        return "yes-agresif", "yes-agresif", 3
    if close > ema50 and cross_today and (cross_yesterday or momentum) and 50 < rsi < 70 and volume_ok:
        return "yes", "yes", 4
    if close > ema50 and cross_today and (cross_yesterday or momentum) and volume < avg_vol:
        return "yes-volume-kurang", "yes-volume-kurang", 5
    return "no", "no", 9

def generate_additional_insight(ticker, harga, ema8, ema20, ema50,
                                 ema8_weekly, ema20_weekly, ema50_weekly):
    trend_pendek = "unknown"
    harga_vs_ema = "unknown"
    weekly_valid = False

    try:
        df = yf.download(f"{ticker}.JK", period='5d', interval='1d')
        closes = df['Close'].dropna().values.tolist()
        
        if len(closes) >= 3:
            if closes[-1] > closes[-2] > closes[-3]:
                trend_pendek = "naik"
            elif closes[-1] < closes[-2] < closes[-3]:
                trend_pendek = "turun"
            else:
                trend_pendek = "netral"

        if harga > ema8 and harga > ema20:
            harga_vs_ema = "di atas semua"
        elif harga > ema20:
            harga_vs_ema = "di atas EMA20"
        elif harga > ema8:
            harga_vs_ema = "di atas EMA8"
        else:
            harga_vs_ema = "di bawah EMA"

        if all(x is not None for x in [ema8_weekly, ema20_weekly, ema50_weekly]):
            if ema8_weekly > ema20_weekly and harga > ema50_weekly:
                weekly_valid = True

    except Exception as e:
        print(f"[generate_additional_insight] Error: {e}")

    return trend_pendek, harga_vs_ema, weekly_valid
    # return {
    #     "trend_pendek": trend_pendek,
    #     "harga_vs_ema": harga_vs_ema,
    #     "weekly_valid": weekly_valid
    # }

# ==========================
# Main Screener Function
# ==========================

def run_screener():
    conn = get_connection()
    cursor = conn.cursor()

    # df_active = pd.read_sql("SELECT ticker FROM ActiveVolumeStocks WHERE active = 1", conn)
    # tickers = [f"{t}.JK" for t in df_active['ticker'].tolist()]
    tickers = get_idx_tickers_from_excel('data/Stock_List.xlsx')
    # tickers = ['GOTO.JK']

    for ticker in tickers:
        df = yf.download(ticker, period='250d', interval='1d')
        if df.empty or len(df) < 30:
            continue

        df = calculate_indicators(df)
        if df.empty or len(df) < 3:
            continue

        # Deteksi waktu lokal WIB
        wib_now = datetime.now(pytz.timezone("Asia/Jakarta"))
        skip_today = wib_now.hour < 15  # Kalau sebelum jam 15:00, jangan pakai data hari ini

        # Jika perlu, buang baris terakhir (data hari ini)
        if skip_today:
            df = df.iloc[:-1]

        if df.empty or len(df) < 3:
            print("skip kosong")
        else:

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            

            breakout_ok = is_valid_breakout(df)
            if breakout_ok:
                entry_type, status, priority = get_entry_type_status_priority(latest, prev)
            else:
                entry_type, status, priority = "no", "no", 9

            ticker_clean = ticker.replace(".JK", "")

            print('--------------------')
            print(ticker.replace(".JK", ""))
            print(latest.name.date())
            print(float(latest['Close']))
            print(round(float(latest['EMA8']), 2))
            print(round(float(latest['EMA20']), 2))
            print(round(float(latest['EMA50']), 2))
            print(round(float(latest['RSI']), 2))
            print(int(latest['Volume']))
            print(int(latest['AvgVolume10']))
            print(status)
            print('--------------------')

            # exit()

            # Insert to ScreeningResults
            cursor.execute("""
                INSERT INTO ScreeningResults (
                    ticker, tanggal, harga, ema8, ema20, ema50, rsi,
                    volume, avg_volume, status_rekomendasi, prioritas,
                    breakout_valid, entry_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker_clean,
                latest.name.date(),
                float(latest['Close']),
                round(float(latest['EMA8']), 2),
                round(float(latest['EMA20']), 2),
                round(float(latest['EMA50']), 2),
                round(float(latest['RSI']), 2),
                int(latest['Volume']),
                int(latest['AvgVolume10']),
                status,
                priority,
                breakout_ok,
                entry_type
            ))

            # Auto insert to WatchlistPersonal jika prioritas 1–2
            if priority in [1, 2]:
                cursor.execute("""
                    INSERT INTO WatchlistPersonal (
                        ticker, tanggal, harga, ema8, ema20, ema50, rsi, volume, avg_volume,
                        prev_ema8, prev_ema20, prev_ema50, prev_rsi, prev_volume, prev_avg_volume,
                        status_rekomendasi, prioritas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker_clean,
                    latest.name.date(),
                    float(latest['Close']),
                    round(float(latest['EMA8']), 2),
                    round(float(latest['EMA20']), 2),
                    round(float(latest['EMA50']), 2),
                    round(float(latest['RSI']), 2),
                    int(latest['Volume']),
                    int(latest['AvgVolume10']),
                    round(float(prev['EMA8']), 2),
                    round(float(prev['EMA20']), 2),
                    round(float(prev['EMA50']), 2),
                    round(float(prev['RSI']), 2),
                    int(prev['Volume']),
                    int(prev['AvgVolume10']),
                    status,
                    priority
                ))


            conn.commit()

    cursor.close()
    conn.close()
    print("Screening selesai.")

if __name__ == "__main__":
    run_screener()
