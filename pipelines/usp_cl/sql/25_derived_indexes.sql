-- Indexes on derived relations (materialized views).
--
-- Split out of 20_constraints.sql because their targets do not exist during
-- 04_index: the pipeline builds base tables first, indexes them, and only
-- then materializes the views that read from them.  Applying these here, at
-- the end of 06_derive, is the earliest point at which the targets exist.
--
-- Extracted from `pg_dump --section=post-data` on 2026-08-08.

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
