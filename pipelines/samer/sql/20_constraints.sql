-- Constraints and secondary indexes on base relations.
--
-- Extracted from `pg_dump --section=post-data` against the live benthic.io
-- database on 2026-08-08.  Primary keys and unique constraints are applied
-- earlier, in 15_keys.sql, because the ingest INSERTs need their arbiter
-- indexes to exist before the first ON CONFLICT fires.
--
-- Indexes whose target is a materialized view live in 25_derived_indexes.sql
-- and are applied in 06_derive, after the views they index have been created.

CREATE INDEX IF NOT EXISTS idx_sam_current ON public.sam_registrations USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_dba_trgm ON public.sam_registrations USING gin (dba_name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_duns ON public.sam_registrations USING btree (duns)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_entity_id ON public.sam_registrations USING btree (entity_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_expiration ON public.sam_registrations USING btree (registration_expiration)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_geom_point ON public.sam_registrations USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_sam_is_current ON public.sam_registrations USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_naics ON public.sam_registrations USING btree (primary_naics)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_name_trgm ON public.sam_registrations USING gin (legal_business_name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_primary_naics ON public.sam_registrations USING btree (primary_naics)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_registrations_geom_point ON public.sam_registrations USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_sam_state ON public.sam_registrations USING btree (physical_state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sam_uei ON public.sam_registrations USING btree (uei)
  TABLESPACE ssd_1tb;
