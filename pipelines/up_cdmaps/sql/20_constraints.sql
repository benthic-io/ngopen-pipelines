-- ============================================================================
-- up_cdmaps: foreign keys and secondary indexes (stage 04_index)
--
-- PROVENANCE: extracted from the live `ucla_polysci_cdmaps` database on 2026-08-08 with
--     pg_dump --schema-only --section=post-data --no-owner --no-privileges \
--             --no-comments -n public ucla_polysci_cdmaps
--
-- Made idempotent: CREATE INDEX -> CREATE INDEX IF NOT EXISTS; ADD CONSTRAINT
-- wrapped in an exception-swallowing DO block. Statements are otherwise
-- verbatim so the audit trail against the live catalog stays exact.
--
-- Primary keys and unique constraints live in 15_keys.sql (applied earlier).
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_cd_congress ON public.congressional_districts USING btree (congress_number);

CREATE INDEX IF NOT EXISTS idx_cd_congress_number ON public.congressional_districts USING btree (congress_number);

CREATE INDEX IF NOT EXISTS idx_cd_congress_state ON public.congressional_districts USING btree (congress_number, statename);

CREATE INDEX IF NOT EXISTS idx_cd_district ON public.congressional_districts USING btree (district);

CREATE INDEX IF NOT EXISTS idx_cd_geom ON public.congressional_districts USING gist (geom);

CREATE INDEX IF NOT EXISTS idx_cd_state ON public.congressional_districts USING btree (statename);

CREATE INDEX IF NOT EXISTS idx_cd_state_congress_district ON public.congressional_districts USING btree (statename, congress_number, district);

CREATE INDEX IF NOT EXISTS idx_cd_statefp ON public.congressional_districts USING btree (statefp);

CREATE INDEX IF NOT EXISTS idx_cd_statename ON public.congressional_districts USING btree (statename);
