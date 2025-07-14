CREATE TABLE WatchlistPersonal_New (
    id INT IDENTITY PRIMARY KEY,
    ticker VARCHAR(20),
    tanggal DATE,

    -- Data teknikal hasil edit manual
    harga FLOAT,
    ema8 FLOAT,
    ema20 FLOAT,
    ema50 FLOAT,
    rsi FLOAT,
    volume BIGINT,
    avg_volume BIGINT,

    -- Data prev
    prev_ema8 FLOAT,
    prev_ema20 FLOAT,
    prev_ema50 FLOAT,
    prev_rsi FLOAT,
    prev_volume BIGINT,
    prev_avg_volume BIGINT,

    -- Weekly (input manual)
    ema8_weekly FLOAT,
    ema20_weekly FLOAT,
    ema50_weekly FLOAT,
    rsi_weekly FLOAT,

	high10 FLOAT,
    low10 FLOAT,

    status_rekomendasi VARCHAR(50),  -- bisa berubah jika indikator diedit
    prioritas INT,

    source_screening_id INT,  -- FK ke ScreeningResults.id (opsional)
    manual_override BIT DEFAULT 0, -- kalau kamu edit sendiri

    created_at DATETIME DEFAULT GETDATE(),
    trend_pendek VARCHAR(MAX) NULL,
    harga_vs_ema VARCHAR(MAX) NULL,
    weekly_valid VARCHAR(MAX) NULL,
	entry_type VARCHAR(50)
);

CREATE INDEX idx_ticker_date ON WatchlistPersonal_New (ticker, tanggal);