-- ============================================================================
-- irs_ng: primary keys and unique constraints (stage 02_restore)
--
-- Split out of 20_constraints.sql because the ingest upserts depend on them:
-- an ON CONFLICT clause needs its arbiter index to already exist. Foreign keys
-- and secondary indexes stay in 20_constraints.sql and are applied later, in
-- 04_index, so the bulk load runs against a lightly indexed table.
--
-- PROVENANCE: extracted from the live `irs_ng` database on 2026-08-08 with
--     pg_dump --schema-only --section=post-data --no-owner --no-privileges \
--             --no-comments -n public irs_ng
-- ============================================================================

DO $$ BEGIN
    ALTER TABLE ONLY public.bmf_organization_snapshots
    ADD CONSTRAINT bmf_organization_snapshots_ein_release_date_release_source_key UNIQUE (ein, release_date, release_source);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.bmf_organization_snapshots
    ADD CONSTRAINT bmf_organization_snapshots_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.bmf_organizations
    ADD CONSTRAINT bmf_organizations_ein_org_name_current_key UNIQUE (ein, org_name_current);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.bmf_organizations
    ADD CONSTRAINT bmf_organizations_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.census_demographics
    ADD CONSTRAINT census_demographics_geoid_year_geo_type_key UNIQUE (geoid, year, geo_type);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.census_demographics
    ADD CONSTRAINT census_demographics_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_details
    ADD CONSTRAINT form990_details_ein_tax_period_key UNIQUE (ein, tax_period);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_details
    ADD CONSTRAINT form990_details_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_schedule_o
    ADD CONSTRAINT form990_schedule_o_ein_tax_period_form_type_key UNIQUE (ein, tax_period, form_type);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_schedule_o
    ADD CONSTRAINT form990_schedule_o_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_soi
    ADD CONSTRAINT form990_soi_ein_tax_year_key UNIQUE (ein, tax_year);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_soi
    ADD CONSTRAINT form990_soi_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_soi_private_foundation
    ADD CONSTRAINT form990_soi_private_foundation_ein_tax_year_key UNIQUE (ein, tax_year);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_soi_private_foundation
    ADD CONSTRAINT form990_soi_private_foundation_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_xml_import_log
    ADD CONSTRAINT form990_xml_import_log_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990_xml_import_log
    ADD CONSTRAINT form990_xml_import_log_zip_filename_key UNIQUE (zip_filename);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990n_small_orgs
    ADD CONSTRAINT form990n_small_orgs_ein_key UNIQUE (ein);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990n_small_orgs
    ADD CONSTRAINT form990n_small_orgs_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990t_details
    ADD CONSTRAINT form990t_details_ein_tax_period_key UNIQUE (ein, tax_period);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.form990t_details
    ADD CONSTRAINT form990t_details_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.political_orgs_527
    ADD CONSTRAINT political_orgs_527_ein_filing_type_key UNIQUE (ein, filing_type);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.political_orgs_527
    ADD CONSTRAINT political_orgs_527_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.pub78_eligible
    ADD CONSTRAINT pub78_eligible_ein_key UNIQUE (ein);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.pub78_eligible
    ADD CONSTRAINT pub78_eligible_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.revoked_organizations
    ADD CONSTRAINT revoked_organizations_ein_key UNIQUE (ein);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.revoked_organizations
    ADD CONSTRAINT revoked_organizations_pkey PRIMARY KEY (id);
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;
