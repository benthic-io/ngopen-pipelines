-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: us_project_cl
-- object:   mv_current_lawmakers
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_current_lawmakers AS
WARNING:  database "us_project_cl" has a collation version mismatch
DETAIL:  The database was created using collation version 2.42, but the operating system provides version 2.43.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE us_project_cl REFRESH COLLATION VERSION, or build PostgreSQL with the right library version.
 SELECT l.bioguide_id,
    l.official_full,
    l.first_name,
    l.last_name,
    l.gender,
    l.birthday,
    lt.state,
    lt.district,
    lt.term_type,
    lt.party,
    lt.term_start,
    lt.term_end,
    lt.class AS senate_class,
    lt.state_rank,
    lt.phone AS office_phone,
    lt.contact_form,
    sm.twitter,
    sm.facebook,
    sm.instagram,
    sm.youtube,
    ( SELECT count(*) AS count
           FROM district_offices doff
          WHERE doff.bioguide_id::text = l.bioguide_id::text) AS office_count,
    ( SELECT count(*) AS count
           FROM committee_membership cm
          WHERE cm.bioguide_id::text = l.bioguide_id::text) AS committee_count
   FROM legislators l
     JOIN legislator_terms lt ON l.bioguide_id::text = lt.bioguide_id::text
     LEFT JOIN legislator_social_media sm ON l.bioguide_id::text = sm.bioguide_id::text
  WHERE l.is_current = true AND lt.term_end >= CURRENT_DATE
WITH NO DATA;
