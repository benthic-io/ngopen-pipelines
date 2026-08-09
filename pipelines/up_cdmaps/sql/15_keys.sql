-- ============================================================================
-- up_cdmaps: primary keys and unique constraints (stage 02_restore)
--
-- Split out of 20_constraints.sql because the ingest upserts depend on them:
-- an ON CONFLICT clause needs its arbiter index to already exist. Foreign keys
-- and secondary indexes stay in 20_constraints.sql and are applied later, in
-- 04_index, so the bulk load runs against a lightly indexed table.
--
-- PROVENANCE: extracted from the live `ucla_polysci_cdmaps` database on 2026-08-08 with
--     pg_dump --schema-only --section=post-data --no-owner --no-privileges \
--             --no-comments -n public ucla_polysci_cdmaps
-- ============================================================================

DO $$ BEGIN
    ALTER TABLE ONLY public.congressional_districts
    ADD CONSTRAINT congressional_districts_congress_number_district_id_key UNIQUE (congress_number, district_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.congressional_districts
    ADD CONSTRAINT congressional_districts_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;
