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


-- public.congressional_districts
CREATE INDEX IF NOT EXISTS idx_cd_congress_number ON public.congressional_districts USING btree (congress_number);
CREATE INDEX IF NOT EXISTS idx_cd_district ON public.congressional_districts USING btree (district);
CREATE INDEX IF NOT EXISTS idx_cd_state_congress_district ON public.congressional_districts USING btree (statename, congress_number, district);
CREATE INDEX IF NOT EXISTS idx_cd_statefp ON public.congressional_districts USING btree (statefp);
CREATE INDEX IF NOT EXISTS idx_cd_statename ON public.congressional_districts USING btree (statename);
