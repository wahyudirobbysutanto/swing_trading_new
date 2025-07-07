import pandas as pd

def get_idx_tickers_from_excel(filepath='data/Daftar Saham.xlsx'):
    try:
        df = pd.read_excel(filepath)
        
        # Pastikan kolom 'Code' ada
        if 'Code' not in df.columns:
            raise ValueError("Kolom 'Code' tidak ditemukan di file Excel.")
        
        tickers = df['Code'].dropna().astype(str).str.strip() + '.JK'
        return tickers.tolist()
    
    except Exception as e:
        print(f"Gagal membaca ticker dari Excel: {e}")
        return []
    