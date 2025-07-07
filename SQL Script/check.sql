
select * from ScreeningResults
order by id desc
--where prioritas in (1, 2)


select * from WatchlistPersonal

select * from AIRecommendations



/*
DELETE FROM ScreeningResults
DELETE FROM WatchlistPersonal


DBCC CHECKIDENT ('dbo.ScreeningResults', RESEED, 954);
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
