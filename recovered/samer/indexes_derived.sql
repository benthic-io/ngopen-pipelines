-- RECOVERED INDEX DDL -- derived objects
-- provenance: recovered
--
-- Indexes on materialized views created by stage 06_derive. Extracted verbatim
-- from pg_indexes on 2026-08-08; no known ETL script creates them.
--
-- Applied at the end of 06_derive, after the views are materialized.


-- public.mv_contractor_registry
CREATE INDEX IF NOT EXISTS idx_mcr_duns ON public.mv_contractor_registry USING btree (duns);
CREATE INDEX IF NOT EXISTS idx_mcr_expiration ON public.mv_contractor_registry USING btree (registration_expiration);
CREATE INDEX IF NOT EXISTS idx_mcr_geom ON public.mv_contractor_registry USING gist (geom_point) WHERE (geom_point IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_mcr_naics ON public.mv_contractor_registry USING btree (primary_naics);
CREATE INDEX IF NOT EXISTS idx_mcr_name_trgm ON public.mv_contractor_registry USING gin (legal_business_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mcr_state ON public.mv_contractor_registry USING btree (physical_state);
CREATE INDEX IF NOT EXISTS idx_mcr_status ON public.mv_contractor_registry USING btree (registration_status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcr_uei ON public.mv_contractor_registry USING btree (uei);
