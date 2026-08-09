-- RECOVERED INDEX DDL
-- provenance: recovered
--
-- Indexes present in the live benthic.io database `sam_er` that are NOT created
-- by any known ETL script. Extracted verbatim from pg_indexes on 2026-08-08.
-- Constraint-backed indexes (*_pkey, *_key) are excluded: they are created
-- implicitly by their table definitions.
--
-- Redundant pairs deliberately preserved here for audit fidelity; see
-- MIGRATION.md for the de-duplication plan.


-- public.mv_contractor_registry
CREATE INDEX IF NOT EXISTS idx_mcr_duns ON public.mv_contractor_registry USING btree (duns);
CREATE INDEX IF NOT EXISTS idx_mcr_expiration ON public.mv_contractor_registry USING btree (registration_expiration);
CREATE INDEX IF NOT EXISTS idx_mcr_geom ON public.mv_contractor_registry USING gist (geom_point) WHERE (geom_point IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_mcr_naics ON public.mv_contractor_registry USING btree (primary_naics);
CREATE INDEX IF NOT EXISTS idx_mcr_name_trgm ON public.mv_contractor_registry USING gin (legal_business_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mcr_state ON public.mv_contractor_registry USING btree (physical_state);
CREATE INDEX IF NOT EXISTS idx_mcr_status ON public.mv_contractor_registry USING btree (registration_status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcr_uei ON public.mv_contractor_registry USING btree (uei);

-- public.sam_registrations
CREATE INDEX IF NOT EXISTS idx_sam_dba_trgm ON public.sam_registrations USING gin (dba_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_sam_duns ON public.sam_registrations USING btree (duns);
CREATE INDEX IF NOT EXISTS idx_sam_entity_id ON public.sam_registrations USING btree (entity_id);
CREATE INDEX IF NOT EXISTS idx_sam_expiration ON public.sam_registrations USING btree (registration_expiration);
CREATE INDEX IF NOT EXISTS idx_sam_is_current ON public.sam_registrations USING btree (is_current);
CREATE INDEX IF NOT EXISTS idx_sam_name_trgm ON public.sam_registrations USING gin (legal_business_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_sam_primary_naics ON public.sam_registrations USING btree (primary_naics);
CREATE INDEX IF NOT EXISTS idx_sam_registrations_geom_point ON public.sam_registrations USING gist (geom_point) WHERE (geom_point IS NOT NULL);
