-- RECOVERED INDEX DDL
-- provenance: recovered
--
-- Indexes present in the live benthic.io database `us_project_cl` that are NOT created
-- by any known ETL script. Extracted verbatim from pg_indexes on 2026-08-08.
-- Constraint-backed indexes (*_pkey, *_key) are excluded: they are created
-- implicitly by their table definitions.
--
-- Redundant pairs deliberately preserved here for audit fidelity; see
-- MIGRATION.md for the de-duplication plan.


-- public.committee_membership
CREATE INDEX IF NOT EXISTS idx_cm_bioguide_id ON public.committee_membership USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_cm_thomas_id ON public.committee_membership USING btree (committee_thomas_id);
CREATE INDEX IF NOT EXISTS idx_cm_title ON public.committee_membership USING btree (title);

-- public.committees
CREATE INDEX IF NOT EXISTS idx_com_is_current ON public.committees USING btree (is_current);
CREATE INDEX IF NOT EXISTS idx_com_name_trgm ON public.committees USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_com_thomas_id ON public.committees USING btree (thomas_id);
CREATE INDEX IF NOT EXISTS idx_com_type ON public.committees USING btree (committee_type);

-- public.district_offices
CREATE INDEX IF NOT EXISTS idx_district_offices_geom_point ON public.district_offices USING gist (geom_point) WHERE (geom_point IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_do_bioguide_id ON public.district_offices USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_do_geom_point ON public.district_offices USING gist (geom_point) WHERE (geom_point IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_do_state ON public.district_offices USING btree (state);

-- public.executive_terms
CREATE INDEX IF NOT EXISTS idx_et_bioguide_id ON public.executive_terms USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_et_start_date ON public.executive_terms USING btree (start_date);

-- public.executives
CREATE INDEX IF NOT EXISTS idx_exec_govtrack_id ON public.executives USING btree (govtrack_id);
CREATE INDEX IF NOT EXISTS idx_exec_name_trgm ON public.executives USING gin (last_name gin_trgm_ops);

-- public.legislator_other_names
CREATE INDEX IF NOT EXISTS idx_lon_bioguide_id ON public.legislator_other_names USING btree (bioguide_id);

-- public.legislator_social_media
CREATE INDEX IF NOT EXISTS idx_lsm_bioguide_id ON public.legislator_social_media USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_lsm_twitter ON public.legislator_social_media USING btree (twitter);

-- public.legislator_terms
CREATE INDEX IF NOT EXISTS idx_lt_bioguide_id ON public.legislator_terms USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_lt_congress ON public.legislator_terms USING btree (congress_start);
CREATE INDEX IF NOT EXISTS idx_lt_state ON public.legislator_terms USING btree (state);
CREATE INDEX IF NOT EXISTS idx_lt_state_district ON public.legislator_terms USING btree (state, district);
CREATE INDEX IF NOT EXISTS idx_lt_state_district_term ON public.legislator_terms USING btree (state, district, term_end);
CREATE INDEX IF NOT EXISTS idx_lt_term_end ON public.legislator_terms USING btree (term_end);
CREATE INDEX IF NOT EXISTS idx_lt_term_type ON public.legislator_terms USING btree (term_type);

-- public.legislators
CREATE INDEX IF NOT EXISTS idx_leg_govtrack_id ON public.legislators USING btree (govtrack_id);
CREATE INDEX IF NOT EXISTS idx_leg_is_current ON public.legislators USING btree (is_current);
CREATE INDEX IF NOT EXISTS idx_leg_last_name_trgm ON public.legislators USING gin (last_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_leg_name_trgm ON public.legislators USING gin (official_full gin_trgm_ops);

-- public.mv_committee_power
CREATE INDEX IF NOT EXISTS idx_mcp_bioguide ON public.mv_committee_power USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_mcp_party ON public.mv_committee_power USING btree (party);
CREATE INDEX IF NOT EXISTS idx_mcp_state_dist ON public.mv_committee_power USING btree (state, district);
CREATE INDEX IF NOT EXISTS idx_mcp_thomas ON public.mv_committee_power USING btree (thomas_id);
CREATE INDEX IF NOT EXISTS idx_mcp_title ON public.mv_committee_power USING btree (title);

-- public.mv_current_lawmakers
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcl_bioguide ON public.mv_current_lawmakers USING btree (bioguide_id);
CREATE INDEX IF NOT EXISTS idx_mcl_district ON public.mv_current_lawmakers USING btree (state, district);
CREATE INDEX IF NOT EXISTS idx_mcl_name_trgm ON public.mv_current_lawmakers USING gin (official_full gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mcl_party ON public.mv_current_lawmakers USING btree (party);
CREATE INDEX IF NOT EXISTS idx_mcl_state ON public.mv_current_lawmakers USING btree (state);
CREATE INDEX IF NOT EXISTS idx_mcl_term_end ON public.mv_current_lawmakers USING btree (term_end);
CREATE INDEX IF NOT EXISTS idx_mcl_term_type ON public.mv_current_lawmakers USING btree (term_type);

-- public.subcommittees
CREATE INDEX IF NOT EXISTS idx_sub_committee_id ON public.subcommittees USING btree (committee_id);
CREATE INDEX IF NOT EXISTS idx_sub_thomas_id ON public.subcommittees USING btree (thomas_id);
