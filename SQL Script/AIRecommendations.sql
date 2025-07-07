CREATE TABLE AIRecommendations (
    id INT IDENTITY PRIMARY KEY,
    ticker VARCHAR(20),
    tanggal DATE,
    versi VARCHAR(50), -- 'user_data' atau 'ai_own_data'
    rekomendasi VARCHAR(50), -- 'Layak', 'Tidak Layak', dll.
    penjelasan TEXT,
    source_data TEXT, -- bisa JSON ringkas dari inputnya

    watchlist_id INT, -- FK ke WatchlistPersonal.id
    created_at DATETIME DEFAULT GETDATE()
);