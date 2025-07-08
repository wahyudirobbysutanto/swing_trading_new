CREATE TABLE ScreeningResults_New (
    id INT IDENTITY PRIMARY KEY,
    ticker VARCHAR(20),
    tanggal DATE,
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

    status_rekomendasi VARCHAR(100),
    prioritas INT,
    breakout_valid BIT,
    entry_type VARCHAR(MAX),
    high10 FLOAT,
    low10 FLOAT,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_ticker_date UNIQUE (ticker, tanggal)
);