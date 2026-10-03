-- Constraints and secondary indexes on base relations.
--
-- Extracted from `pg_dump --section=post-data` against the live benthic.io
-- database on 2026-08-08.  Primary keys and unique constraints are applied
-- earlier, in 15_keys.sql, because the ingest INSERTs need their arbiter
-- indexes to exist before the first ON CONFLICT fires.
--
-- Indexes whose target is a materialized view live in 25_derived_indexes.sql
-- and are applied in 06_derive, after the views they index have been created.

CREATE INDEX IF NOT EXISTS idx_cd_congress ON public.congressional_districts USING btree (congress_number)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_congress_number ON public.congressional_districts USING btree (congress_number)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_congress_state ON public.congressional_districts USING btree (congress_number, statename)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_district ON public.congressional_districts USING btree (district)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_geom ON public.congressional_districts USING gist (geom)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_state ON public.congressional_districts USING btree (statename)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_state_congress_district ON public.congressional_districts USING btree (statename, congress_number, district)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_statefp ON public.congressional_districts USING btree (statefp)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cd_statename ON public.congressional_districts USING btree (statename)
  TABLESPACE ssd_1tb;
