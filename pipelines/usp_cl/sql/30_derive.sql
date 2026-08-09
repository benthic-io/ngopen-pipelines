-- ============================================================================
-- usp_cl: derived objects -- views, materialized views, RPC functions
-- (stage 06_derive)
--
-- PROVENANCE: extracted from the live `us_project_cl` catalog on 2026-08-08.
-- Several of these objects have NO source in the legacy ngopen scripts; they
-- were created by hand in psql and are recovered here so the pipeline is
-- reproducible. The per-object recovered/ files carry individual provenance
-- headers; this file is the ordered, runnable form.
--
-- Idempotent: CREATE FUNCTION -> CREATE OR REPLACE FUNCTION, materialized
-- views use IF NOT EXISTS and are populated by the stage's REFRESH.
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_committee_power AS
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
   FROM ((public.committees c
     JOIN public.committee_membership cm ON (((c.thomas_id)::text = (cm.committee_thomas_id)::text)))
     JOIN public.legislator_terms lt ON (((cm.bioguide_id)::text = (lt.bioguide_id)::text)))
  WHERE ((c.is_current = true) AND (lt.term_end >= CURRENT_DATE))
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_current_lawmakers AS
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
           FROM public.district_offices doff
          WHERE ((doff.bioguide_id)::text = (l.bioguide_id)::text)) AS office_count,
    ( SELECT count(*) AS count
           FROM public.committee_membership cm
          WHERE ((cm.bioguide_id)::text = (l.bioguide_id)::text)) AS committee_count
   FROM ((public.legislators l
     JOIN public.legislator_terms lt ON (((l.bioguide_id)::text = (lt.bioguide_id)::text)))
     LEFT JOIN public.legislator_social_media sm ON (((l.bioguide_id)::text = (sm.bioguide_id)::text)))
  WHERE ((l.is_current = true) AND (lt.term_end >= CURRENT_DATE))
  WITH NO DATA;
