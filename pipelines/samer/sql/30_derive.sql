-- ============================================================================
-- samer: derived objects -- views, materialized views, RPC functions
-- (stage 06_derive)
--
-- PROVENANCE: extracted from the live `sam_er` catalog on 2026-08-08.
-- Several of these objects have NO source in the legacy ngopen scripts; they
-- were created by hand in psql and are recovered here so the pipeline is
-- reproducible. The per-object recovered/ files carry individual provenance
-- headers; this file is the ordered, runnable form.
--
-- Idempotent: CREATE FUNCTION -> CREATE OR REPLACE FUNCTION, materialized
-- views use IF NOT EXISTS and are populated by the stage's REFRESH.
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_contractor_registry AS
 SELECT uei,
    entity_id,
    duns,
    legal_business_name,
    dba_name,
    primary_naics,
    naics_codes,
    psc_codes,
    physical_city,
    physical_state,
    physical_zip,
    physical_country,
    latitude,
    longitude,
    geom_point,
    registration_expiration,
    last_update,
    business_start_date,
    corporate_url,
    purpose_of_registration,
        CASE
            WHEN ((registration_expiration IS NOT NULL) AND ((registration_expiration)::text < to_char((CURRENT_DATE + '90 days'::interval), 'YYYYMMDD'::text))) THEN 'expiring_soon'::text
            WHEN ((registration_expiration IS NOT NULL) AND ((registration_expiration)::text < to_char((CURRENT_DATE)::timestamp with time zone, 'YYYYMMDD'::text))) THEN 'expired'::text
            ELSE 'active'::text
        END AS registration_status
   FROM public.sam_registrations
  WHERE (is_current = true)
  WITH NO DATA;
