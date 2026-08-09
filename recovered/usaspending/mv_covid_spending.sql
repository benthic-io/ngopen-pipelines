-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: usaspending_db
-- object:   mv_covid_spending
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_covid_spending AS
WARNING:  database "usaspending_db" has a collation version mismatch
DETAIL:  The database was created using collation version 2.42, but the operating system provides version 2.43.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE usaspending_db REFRESH COLLATION VERSION, or build PostgreSQL with the right library version.
 SELECT fiscal_year,
    count(DISTINCT award_id) AS award_count,
    sum(total_covid_obligation) AS total_covid_obligation,
    sum(total_covid_outlay) AS total_covid_outlay,
    count(DISTINCT recipient_uei) AS unique_recipients,
    count(DISTINCT awarding_agency_code) AS unique_agencies
   FROM prime_awards
  WHERE total_covid_obligation IS NOT NULL AND total_covid_obligation > 0::numeric
  GROUP BY fiscal_year
WITH NO DATA;
