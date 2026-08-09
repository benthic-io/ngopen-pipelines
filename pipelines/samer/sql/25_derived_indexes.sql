-- Indexes on derived relations (materialized views).
--
-- Split out of 20_constraints.sql because their targets do not exist during
-- 04_index: the pipeline builds base tables first, indexes them, and only
-- then materializes the views that read from them.  Applying these here, at
-- the end of 06_derive, is the earliest point at which the targets exist.
--
-- Extracted from `pg_dump --section=post-data` on 2026-08-08.

CREATE INDEX IF NOT EXISTS idx_mcr_duns ON public.mv_contractor_registry USING btree (duns);

CREATE INDEX IF NOT EXISTS idx_mcr_expiration ON public.mv_contractor_registry USING btree (registration_expiration);

CREATE INDEX IF NOT EXISTS idx_mcr_geom ON public.mv_contractor_registry USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_mcr_naics ON public.mv_contractor_registry USING btree (primary_naics);

CREATE INDEX IF NOT EXISTS idx_mcr_name_trgm ON public.mv_contractor_registry USING gin (legal_business_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_mcr_state ON public.mv_contractor_registry USING btree (physical_state);

CREATE INDEX IF NOT EXISTS idx_mcr_status ON public.mv_contractor_registry USING btree (registration_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mcr_uei ON public.mv_contractor_registry USING btree (uei);

CREATE INDEX IF NOT EXISTS idx_mv_contractor_geom ON public.mv_contractor_registry USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_mv_contractor_state ON public.mv_contractor_registry USING btree (physical_state);

CREATE INDEX IF NOT EXISTS idx_mv_contractor_status ON public.mv_contractor_registry USING btree (registration_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_contractor_uei ON public.mv_contractor_registry USING btree (uei);
