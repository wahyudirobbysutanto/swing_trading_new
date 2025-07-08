import yfinance as yf
import pandas as pd
from db import get_connection
from datetime import datetime
from utils import get_idx_tickers_from_excel

def update_daily_price():
    conn = get_connection()
    cursor = conn.cursor()

    tickers = get_idx_tickers_from_excel('data/Stock_List.xlsx')

    for ticker in tickers:
        df = yf.download(ticker, period='250d', interval='1d')
        df = df.reset_index()
        print(ticker.replace(".JK", ""))

        for _, row in df.iterrows():
            # print(row['Date'].item().date())
            # print(row['Open'])
            # print(row['High'])
            # print(row['Low'])
            # print(row['Close'])
            # print(row['Volume'])
            # exit()
            tanggal = row['Date'].item().date()
            ticker_clean = ticker.replace(".JK", "")

            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM DailyPrice WHERE ticker = ? AND tanggal = ?
                )
                INSERT INTO DailyPrice (ticker, tanggal, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker_clean, tanggal,
                ticker_clean, tanggal, row['Open'].item(), row['High'].item(), row['Low'].item(), row['Close'].item(), int(row['Volume'].item())
            ))

    conn.commit()
    conn.close()
    print("Update selesai.")

if __name__ == "__main__":
    update_daily_price()
