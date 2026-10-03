-- Constraints and secondary indexes on base relations.
--
-- Extracted from `pg_dump --section=post-data` against the live benthic.io
-- database on 2026-08-08.  Primary keys and unique constraints are applied
-- earlier, in 15_keys.sql, because the ingest INSERTs need their arbiter
-- indexes to exist before the first ON CONFLICT fires.
--
-- Indexes whose target is a materialized view live in 25_derived_indexes.sql
-- and are applied in 06_derive, after the views they index have been created.

CREATE INDEX IF NOT EXISTS idx_cm_bioguide_id ON public.committee_membership USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cm_thomas_id ON public.committee_membership USING btree (committee_thomas_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_cm_title ON public.committee_membership USING btree (title)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_com_is_current ON public.committees USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_com_name_trgm ON public.committees USING gin (name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_com_thomas_id ON public.committees USING btree (thomas_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_com_type ON public.committees USING btree (committee_type)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_committees_current ON public.committees USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_committees_thomas ON public.committees USING btree (thomas_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_committees_type ON public.committees USING btree (committee_type)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_district_offices_geom_point ON public.district_offices USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_do_bioguide_id ON public.district_offices USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_do_geom_point ON public.district_offices USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_do_state ON public.district_offices USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_et_bioguide_id ON public.executive_terms USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_et_start_date ON public.executive_terms USING btree (start_date)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_exec_govtrack_id ON public.executives USING btree (govtrack_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_exec_name_trgm ON public.executives USING gin (last_name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_leg_govtrack_id ON public.legislators USING btree (govtrack_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_leg_is_current ON public.legislators USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_leg_last_name_trgm ON public.legislators USING gin (last_name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_leg_name_trgm ON public.legislators USING gin (official_full public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_legislators_first_name ON public.legislators USING btree (first_name)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_legislators_full_name ON public.legislators USING btree (official_full)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_legislators_full_name_trgm ON public.legislators USING gin (official_full public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_legislators_is_current ON public.legislators USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_legislators_last_name ON public.legislators USING btree (last_name)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lon_bioguide_id ON public.legislator_other_names USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lsm_bioguide_id ON public.legislator_social_media USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lsm_twitter ON public.legislator_social_media USING btree (twitter)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_bioguide_id ON public.legislator_terms USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_congress ON public.legislator_terms USING btree (congress_start)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_state ON public.legislator_terms USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_state_district ON public.legislator_terms USING btree (state, district)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_state_district_term ON public.legislator_terms USING btree (state, district, term_end)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_term_end ON public.legislator_terms USING btree (term_end)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_lt_term_type ON public.legislator_terms USING btree (term_type)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_membership_bioguide ON public.committee_membership USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_membership_committee ON public.committee_membership USING btree (committee_thomas_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_offices_bioguide ON public.district_offices USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_offices_city ON public.district_offices USING btree (city)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_offices_location ON public.district_offices USING btree (latitude, longitude)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_offices_state ON public.district_offices USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sub_committee_id ON public.subcommittees USING btree (committee_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_sub_thomas_id ON public.subcommittees USING btree (thomas_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_bioguide ON public.legislator_terms USING btree (bioguide_id)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_congress ON public.legislator_terms USING btree (congress_start, congress_end)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_dates ON public.legislator_terms USING btree (term_start, term_end)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_district ON public.legislator_terms USING btree (district)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_state ON public.legislator_terms USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_state_district_congress ON public.legislator_terms USING btree (state, district, congress_start, congress_end)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_terms_type_state ON public.legislator_terms USING btree (term_type, state)
  TABLESPACE ssd_1tb;

DO $$ BEGIN
    ALTER TABLE ONLY public.district_offices
    ADD CONSTRAINT district_offices_bioguide_id_fkey FOREIGN KEY (bioguide_id) REFERENCES public.legislators(bioguide_id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.executive_terms
    ADD CONSTRAINT executive_terms_bioguide_id_fkey FOREIGN KEY (bioguide_id) REFERENCES public.executives(bioguide_id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislator_other_names
    ADD CONSTRAINT legislator_other_names_bioguide_id_fkey FOREIGN KEY (bioguide_id) REFERENCES public.legislators(bioguide_id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislator_social_media
    ADD CONSTRAINT legislator_social_media_bioguide_id_fkey FOREIGN KEY (bioguide_id) REFERENCES public.legislators(bioguide_id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.legislator_terms
    ADD CONSTRAINT legislator_terms_bioguide_id_fkey FOREIGN KEY (bioguide_id) REFERENCES public.legislators(bioguide_id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE ONLY public.subcommittees
    ADD CONSTRAINT subcommittees_committee_id_fkey FOREIGN KEY (committee_id) REFERENCES public.committees(committee_id) ON DELETE CASCADE;
EXCEPTION WHEN duplicate_table OR duplicate_object OR invalid_table_definition THEN NULL;
END $$;
