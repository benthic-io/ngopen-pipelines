-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: us_project_cl
-- object:   mv_committee_power
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_committee_power AS
WARNING:  database "us_project_cl" has a collation version mismatch
DETAIL:  The database was created using collation version 2.42, but the operating system provides version 2.43.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE us_project_cl REFRESH COLLATION VERSION, or build PostgreSQL with the right library version.
 SELECT c.committee_id,
    c.thomas_id,
    c.name AS committee_name,
    c.committee_type,
    c.is_current,
    cm.bioguide_id,
    cm.legislator_name,
    cm.party,
    cm.rank,
    cm.title,
    lt.state,
    lt.district,
    lt.term_end
   FROM committees c
     JOIN committee_membership cm ON c.thomas_id::text = cm.committee_thomas_id::text
     JOIN legislator_terms lt ON cm.bioguide_id::text = lt.bioguide_id::text
  WHERE c.is_current = true AND lt.term_end >= CURRENT_DATE
WITH NO DATA;
