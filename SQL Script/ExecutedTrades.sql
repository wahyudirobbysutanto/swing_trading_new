CREATE TABLE ExecutedTrades (
    id INT IDENTITY PRIMARY KEY,
    ticker VARCHAR(20),
    tanggal_beli DATE,
    harga_beli FLOAT,
    jumlah_lot INT,

    tp FLOAT,
    cl FLOAT,

    status_posisi VARCHAR(20), -- 'Open', 'TP', 'CL', 'Hold', dll.
    tanggal_close DATE,
    harga_close FLOAT,

    watchlist_id INT, -- FK ke WatchlistPersonal.id (opsional)
    created_at DATETIME DEFAULT GETDATE()
);
