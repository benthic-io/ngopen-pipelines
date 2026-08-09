-- ============================================================================
-- samer: foreign keys and secondary indexes (stage 04_index)
--
-- PROVENANCE: extracted from the live `sam_er` database on 2026-08-08 with
--     pg_dump --schema-only --section=post-data --no-owner --no-privileges \
--             --no-comments -n public sam_er
--
-- Made idempotent: CREATE INDEX -> CREATE INDEX IF NOT EXISTS; ADD CONSTRAINT
-- wrapped in an exception-swallowing DO block. Statements are otherwise
-- verbatim so the audit trail against the live catalog stays exact.
--
-- Primary keys and unique constraints live in 15_keys.sql (applied earlier).
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_sam_current ON public.sam_registrations USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_sam_dba_trgm ON public.sam_registrations USING gin (dba_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sam_duns ON public.sam_registrations USING btree (duns);

CREATE INDEX IF NOT EXISTS idx_sam_entity_id ON public.sam_registrations USING btree (entity_id);

CREATE INDEX IF NOT EXISTS idx_sam_expiration ON public.sam_registrations USING btree (registration_expiration);

CREATE INDEX IF NOT EXISTS idx_sam_geom_point ON public.sam_registrations USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_sam_is_current ON public.sam_registrations USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_sam_naics ON public.sam_registrations USING btree (primary_naics);

CREATE INDEX IF NOT EXISTS idx_sam_name_trgm ON public.sam_registrations USING gin (legal_business_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sam_primary_naics ON public.sam_registrations USING btree (primary_naics);

CREATE INDEX IF NOT EXISTS idx_sam_registrations_geom_point ON public.sam_registrations USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_sam_state ON public.sam_registrations USING btree (physical_state);

CREATE INDEX IF NOT EXISTS idx_sam_uei ON public.sam_registrations USING btree (uei);
