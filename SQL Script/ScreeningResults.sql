CREATE TABLE ScreeningResults (
    id INT IDENTITY PRIMARY KEY,
    ticker VARCHAR(20),
    tanggal DATE, -- tanggal harga (dari Yahoo)
    harga FLOAT,
    ema8 FLOAT,
    ema20 FLOAT,
    ema50 FLOAT,
    rsi FLOAT,
    volume BIGINT,
    avg_volume BIGINT,
    status_rekomendasi VARCHAR(50),
    prioritas INT, -- 1, 2, 3, dst.
    breakout_valid BIT,
    entry_type VARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE()
);