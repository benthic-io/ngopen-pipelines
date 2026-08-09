-- RECOVERED INDEX DDL -- derived objects
-- provenance: recovered
--
-- Indexes on materialized views created by stage 06_derive. Extracted verbatim
-- from pg_indexes on 2026-08-08; no known ETL script creates them.
--
-- Applied at the end of 06_derive, after the views are materialized.


-- public.mv_nonprofit_profile
CREATE INDEX IF NOT EXISTS idx_mnp_geom ON public.mv_nonprofit_profile USING gist (geom_point) WHERE (geom_point IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_mnp_name_trgm ON public.mv_nonprofit_profile USING gin (org_name_current gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mnp_ntee ON public.mv_nonprofit_profile USING btree (ntee_irs);
CREATE INDEX IF NOT EXISTS idx_mnp_revenue ON public.mv_nonprofit_profile USING btree (recent_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_mnp_revoked ON public.mv_nonprofit_profile USING btree (revocation_date) WHERE (revocation_date IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_mnp_state ON public.mv_nonprofit_profile USING btree (f990_org_addr_state);
CREATE INDEX IF NOT EXISTS idx_mnp_subsection ON public.mv_nonprofit_profile USING btree (bmf_subsection_code);

-- public.mv_org_financial_health
CREATE UNIQUE INDEX IF NOT EXISTS idx_mfh_ein ON public.mv_org_financial_health USING btree (ein);
CREATE INDEX IF NOT EXISTS idx_mfh_health ON public.mv_org_financial_health USING btree (financial_health);
CREATE INDEX IF NOT EXISTS idx_mfh_revenue ON public.mv_org_financial_health USING btree (avg_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_mfh_years ON public.mv_org_financial_health USING btree (years_of_data);
