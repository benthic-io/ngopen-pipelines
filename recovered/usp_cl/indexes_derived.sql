-- RECOVERED INDEX DDL -- derived objects
-- provenance: recovered
--
-- Indexes on materialized views created by stage 06_derive. Extracted verbatim
-- from pg_indexes on 2026-08-08; no known ETL script creates them.
--
-- Applied at the end of 06_derive, after the views are materialized.


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
