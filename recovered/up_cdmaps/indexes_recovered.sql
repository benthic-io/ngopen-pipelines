-- RECOVERED INDEX DDL
-- provenance: recovered
--
-- Indexes present in the live benthic.io database `ucla_polysci_cdmaps` that are NOT created
-- by any known ETL script. Extracted verbatim from pg_indexes on 2026-08-08.
-- Constraint-backed indexes (*_pkey, *_key) are excluded: they are created
-- implicitly by their table definitions.
--
-- Redundant pairs deliberately preserved here for audit fidelity; see
-- MIGRATION.md for the de-duplication plan.


-- public.congressional_districts
CREATE INDEX IF NOT EXISTS idx_cd_congress_number ON public.congressional_districts USING btree (congress_number);
CREATE INDEX IF NOT EXISTS idx_cd_district ON public.congressional_districts USING btree (district);
CREATE INDEX IF NOT EXISTS idx_cd_state_congress_district ON public.congressional_districts USING btree (statename, congress_number, district);
CREATE INDEX IF NOT EXISTS idx_cd_statefp ON public.congressional_districts USING btree (statefp);
CREATE INDEX IF NOT EXISTS idx_cd_statename ON public.congressional_districts USING btree (statename);
