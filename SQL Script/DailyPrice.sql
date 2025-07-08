CREATE TABLE DailyPrice (
    ticker VARCHAR(20),
    tanggal DATE,
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    volume BIGINT,
    PRIMARY KEY (ticker, tanggal)
);
