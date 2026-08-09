-- ============================================================================
-- usp_cl: primary keys and unique constraints (stage 02_restore)
--
-- Split out of 20_constraints.sql because the ingest upserts depend on them:
-- an ON CONFLICT clause needs its arbiter index to already exist. Foreign keys
-- and secondary indexes stay in 20_constraints.sql and are applied later, in
-- 04_index, so the bulk load runs against a lightly indexed table.
--
-- PROVENANCE: extracted from the live `us_project_cl` database on 2026-08-08 with
--     pg_dump --schema-only --section=post-data --no-owner --no-privileges \
--             --no-comments -n public us_project_cl
-- ============================================================================

DO $$ BEGIN
    ALTER TABLE ONLY public.committee_membership
    ADD CONSTRAINT committee_membership_pkey PRIMARY KEY (membership_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.committees
    ADD CONSTRAINT committees_pkey PRIMARY KEY (committee_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.district_offices
    ADD CONSTRAINT district_offices_pkey PRIMARY KEY (office_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.executive_terms
    ADD CONSTRAINT executive_terms_pkey PRIMARY KEY (term_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.executives
    ADD CONSTRAINT executives_pkey PRIMARY KEY (bioguide_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislator_other_names
    ADD CONSTRAINT legislator_other_names_pkey PRIMARY KEY (name_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislator_social_media
    ADD CONSTRAINT legislator_social_media_pkey PRIMARY KEY (social_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislator_terms
    ADD CONSTRAINT legislator_terms_pkey PRIMARY KEY (term_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislators
    ADD CONSTRAINT legislators_pkey PRIMARY KEY (bioguide_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.subcommittees
    ADD CONSTRAINT subcommittees_pkey PRIMARY KEY (subcommittee_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;
