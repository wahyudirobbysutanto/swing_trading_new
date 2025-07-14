
select * from ScreeningResults
order by id desc
--where prioritas in (1, 2)


select * from WatchlistPersonal

select * from AIRecommendations


SELECT * FROM WatchlistPersonal 
WHERE tanggal = (SELECT MAX(tanggal) FROM WatchlistPersonal)
ORDER BY tanggal DESC





/*
DELETE FROM ScreeningResults
where created_at >= '2025-07-07 21:00:00.000'
DELETE FROM WatchlistPersonal
where tanggal = '2025-07-07'

DBCC CHECKIDENT ('dbo.ScreeningResults', RESEED, 953);
DBCC CHECKIDENT ('dbo.WatchlistPersonal', RESEED, 5);


DELETE FROM AIRecommendations
DBCC CHECKIDENT ('dbo.AIRecommendations', RESEED, 0);

*/

ALTER TABLE ScreeningResults
ALTER COLUMN volume BIGINT;

ALTER TABLE ScreeningResults
ALTER COLUMN avg_volume BIGINT;

ALTER TABLE WatchlistPersonal
ALTER COLUMN volume BIGINT;

ALTER TABLE WatchlistPersonal
ALTER COLUMN avg_volume BIGINT;
