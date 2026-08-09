-- NEW DDL -- not present in the legacy us_project_cl database.
--
-- Eight of the ten tables key on a surrogate serial, so the legacy loader
-- relied on DROP DATABASE to stay idempotent: every run started empty.
-- This pipeline never drops anything, which means every INSERT needs a real
-- arbiter to conflict against. These natural uniques supply one.
--
-- NULLS NOT DISTINCT (PostgreSQL 15+) is required: several of these columns
-- are legitimately NULL in the upstream YAML, and under the default
-- NULLS DISTINCT two NULL-bearing rows would never collide, silently
-- reintroducing the duplication this file exists to prevent.
--
-- Applied by stage 02_restore, before ingest.

DO $$ BEGIN
ALTER TABLE ONLY public.legislator_terms
    ADD CONSTRAINT legislator_terms_natural_key
    UNIQUE NULLS NOT DISTINCT (bioguide_id, term_start, term_type);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.legislator_other_names
    ADD CONSTRAINT legislator_other_names_natural_key
    UNIQUE NULLS NOT DISTINCT (bioguide_id, first_name, last_name, start_date);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.legislator_social_media
    ADD CONSTRAINT legislator_social_media_natural_key
    UNIQUE (bioguide_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.district_offices
    ADD CONSTRAINT district_offices_natural_key
    UNIQUE NULLS NOT DISTINCT (bioguide_id, office_key);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.committees
    ADD CONSTRAINT committees_natural_key
    UNIQUE (thomas_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.subcommittees
    ADD CONSTRAINT subcommittees_natural_key
    UNIQUE NULLS NOT DISTINCT (committee_id, thomas_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.committee_membership
    ADD CONSTRAINT committee_membership_natural_key
    UNIQUE NULLS NOT DISTINCT (committee_thomas_id, bioguide_id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;

DO $$ BEGIN
ALTER TABLE ONLY public.executive_terms
    ADD CONSTRAINT executive_terms_natural_key
    UNIQUE NULLS NOT DISTINCT (bioguide_id, start_date);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL; END $$;
