-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: usaspending_db
-- object:   mv_district_spending
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_district_spending AS
WARNING:  database "usaspending_db" has a collation version mismatch
DETAIL:  The database was created using collation version 2.42, but the operating system provides version 2.43.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE usaspending_db REFRESH COLLATION VERSION, or build PostgreSQL with the right library version.
 SELECT COALESCE(z.state_abbreviation, pa.pop_state) AS state,
    COALESCE(z.congressional_district_no, pa.pop_congressional_district) AS district,
    pa.fiscal_year,
    count(DISTINCT pa.award_id) AS award_count,
    sum(pa.total_obligation) AS total_obligation,
    sum(pa.award_amount) AS total_award_amount,
    count(DISTINCT pa.recipient_name) AS unique_recipients,
    count(DISTINCT pa.awarding_agency) AS unique_agencies
   FROM prime_awards pa
     LEFT JOIN zips_grouped z ON pa.pop_zip5 = z.zip5
  WHERE pa.pop_state IS NOT NULL AND pa.pop_congressional_district IS NOT NULL AND pa.pop_congressional_district <> '90'::text
  GROUP BY (COALESCE(z.state_abbreviation, pa.pop_state)), (COALESCE(z.congressional_district_no, pa.pop_congressional_district)), pa.fiscal_year
WITH NO DATA;
