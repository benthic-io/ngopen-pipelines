-- ============================================================================
-- usp_cl: foreign keys and secondary indexes (stage 04_index)
--
-- PROVENANCE: extracted from the live `us_project_cl` database on 2026-08-08 with
--     pg_dump --schema-only --section=post-data --no-owner --no-privileges \
--             --no-comments -n public us_project_cl
--
-- Made idempotent: CREATE INDEX -> CREATE INDEX IF NOT EXISTS; ADD CONSTRAINT
-- wrapped in an exception-swallowing DO block. Statements are otherwise
-- verbatim so the audit trail against the live catalog stays exact.
--
-- Primary keys and unique constraints live in 15_keys.sql (applied earlier).
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_cm_bioguide_id ON public.committee_membership USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_cm_thomas_id ON public.committee_membership USING btree (committee_thomas_id);

CREATE INDEX IF NOT EXISTS idx_cm_title ON public.committee_membership USING btree (title);

CREATE INDEX IF NOT EXISTS idx_com_is_current ON public.committees USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_com_name_trgm ON public.committees USING gin (name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_com_thomas_id ON public.committees USING btree (thomas_id);

CREATE INDEX IF NOT EXISTS idx_com_type ON public.committees USING btree (committee_type);

CREATE INDEX IF NOT EXISTS idx_committees_current ON public.committees USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_committees_thomas ON public.committees USING btree (thomas_id);

CREATE INDEX IF NOT EXISTS idx_committees_type ON public.committees USING btree (committee_type);

CREATE INDEX IF NOT EXISTS idx_district_offices_geom_point ON public.district_offices USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_do_bioguide_id ON public.district_offices USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_do_geom_point ON public.district_offices USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_do_state ON public.district_offices USING btree (state);

CREATE INDEX IF NOT EXISTS idx_et_bioguide_id ON public.executive_terms USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_et_start_date ON public.executive_terms USING btree (start_date);

CREATE INDEX IF NOT EXISTS idx_exec_govtrack_id ON public.executives USING btree (govtrack_id);

CREATE INDEX IF NOT EXISTS idx_exec_name_trgm ON public.executives USING gin (last_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_leg_govtrack_id ON public.legislators USING btree (govtrack_id);

CREATE INDEX IF NOT EXISTS idx_leg_is_current ON public.legislators USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_leg_last_name_trgm ON public.legislators USING gin (last_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_leg_name_trgm ON public.legislators USING gin (official_full public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_legislators_first_name ON public.legislators USING btree (first_name);

CREATE INDEX IF NOT EXISTS idx_legislators_full_name ON public.legislators USING btree (official_full);

CREATE INDEX IF NOT EXISTS idx_legislators_full_name_trgm ON public.legislators USING gin (official_full public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_legislators_is_current ON public.legislators USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_legislators_last_name ON public.legislators USING btree (last_name);

CREATE INDEX IF NOT EXISTS idx_lon_bioguide_id ON public.legislator_other_names USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_lsm_bioguide_id ON public.legislator_social_media USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_lsm_twitter ON public.legislator_social_media USING btree (twitter);

CREATE INDEX IF NOT EXISTS idx_lt_bioguide_id ON public.legislator_terms USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_lt_congress ON public.legislator_terms USING btree (congress_start);

CREATE INDEX IF NOT EXISTS idx_lt_state ON public.legislator_terms USING btree (state);

CREATE INDEX IF NOT EXISTS idx_lt_state_district ON public.legislator_terms USING btree (state, district);

CREATE INDEX IF NOT EXISTS idx_lt_state_district_term ON public.legislator_terms USING btree (state, district, term_end);

CREATE INDEX IF NOT EXISTS idx_lt_term_end ON public.legislator_terms USING btree (term_end);

CREATE INDEX IF NOT EXISTS idx_lt_term_type ON public.legislator_terms USING btree (term_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mcl_bioguide ON public.mv_current_lawmakers USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_mcl_district ON public.mv_current_lawmakers USING btree (state, district);

CREATE INDEX IF NOT EXISTS idx_mcl_name_trgm ON public.mv_current_lawmakers USING gin (official_full public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_mcl_party ON public.mv_current_lawmakers USING btree (party);

CREATE INDEX IF NOT EXISTS idx_mcl_state ON public.mv_current_lawmakers USING btree (state);

CREATE INDEX IF NOT EXISTS idx_mcl_term_end ON public.mv_current_lawmakers USING btree (term_end);

CREATE INDEX IF NOT EXISTS idx_mcl_term_type ON public.mv_current_lawmakers USING btree (term_type);

CREATE INDEX IF NOT EXISTS idx_mcp_bioguide ON public.mv_committee_power USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_mcp_party ON public.mv_committee_power USING btree (party);

CREATE INDEX IF NOT EXISTS idx_mcp_state_dist ON public.mv_committee_power USING btree (state, district);

CREATE INDEX IF NOT EXISTS idx_mcp_thomas ON public.mv_committee_power USING btree (thomas_id);

CREATE INDEX IF NOT EXISTS idx_mcp_title ON public.mv_committee_power USING btree (title);

CREATE INDEX IF NOT EXISTS idx_membership_bioguide ON public.committee_membership USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_membership_committee ON public.committee_membership USING btree (committee_thomas_id);

CREATE INDEX IF NOT EXISTS idx_offices_bioguide ON public.district_offices USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_offices_city ON public.district_offices USING btree (city);

CREATE INDEX IF NOT EXISTS idx_offices_location ON public.district_offices USING btree (latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_offices_state ON public.district_offices USING btree (state);

CREATE INDEX IF NOT EXISTS idx_sub_committee_id ON public.subcommittees USING btree (committee_id);

CREATE INDEX IF NOT EXISTS idx_sub_thomas_id ON public.subcommittees USING btree (thomas_id);

CREATE INDEX IF NOT EXISTS idx_terms_bioguide ON public.legislator_terms USING btree (bioguide_id);

CREATE INDEX IF NOT EXISTS idx_terms_congress ON public.legislator_terms USING btree (congress_start, congress_end);

CREATE INDEX IF NOT EXISTS idx_terms_dates ON public.legislator_terms USING btree (term_start, term_end);

CREATE INDEX IF NOT EXISTS idx_terms_district ON public.legislator_terms USING btree (district);

CREATE INDEX IF NOT EXISTS idx_terms_state ON public.legislator_terms USING btree (state);

CREATE INDEX IF NOT EXISTS idx_terms_state_district_congress ON public.legislator_terms USING btree (state, district, congress_start, congress_end);

CREATE INDEX IF NOT EXISTS idx_terms_type_state ON public.legislator_terms USING btree (term_type, state);

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
