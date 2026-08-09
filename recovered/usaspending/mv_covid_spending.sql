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
