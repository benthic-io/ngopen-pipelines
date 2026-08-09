-- RECOVERED INDEX DDL -- base relations
-- provenance: recovered
--
-- Indexes present in the live benthic.io database that are NOT created by any
-- known ETL script. Extracted verbatim from pg_indexes on 2026-08-08.
-- Constraint-backed indexes (*_pkey, *_key) are excluded: they are created
-- implicitly by their table definitions.
--
-- Applied in stage 04_index. Indexes whose target is a materialized view built
-- by stage 06_derive live in indexes_derived.sql instead -- they cannot be
-- created here because the relation does not exist yet.
--
-- Redundant pairs deliberately preserved for audit fidelity; see MIGRATION.md.


-- public.sam_registrations
CREATE INDEX IF NOT EXISTS idx_sam_dba_trgm ON public.sam_registrations USING gin (dba_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_sam_duns ON public.sam_registrations USING btree (duns);
CREATE INDEX IF NOT EXISTS idx_sam_entity_id ON public.sam_registrations USING btree (entity_id);
CREATE INDEX IF NOT EXISTS idx_sam_expiration ON public.sam_registrations USING btree (registration_expiration);
CREATE INDEX IF NOT EXISTS idx_sam_is_current ON public.sam_registrations USING btree (is_current);
CREATE INDEX IF NOT EXISTS idx_sam_name_trgm ON public.sam_registrations USING gin (legal_business_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_sam_primary_naics ON public.sam_registrations USING btree (primary_naics);
CREATE INDEX IF NOT EXISTS idx_sam_registrations_geom_point ON public.sam_registrations USING gist (geom_point) WHERE (geom_point IS NOT NULL);
