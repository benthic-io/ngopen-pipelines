-- Indexes on derived relations (materialized views).
--
-- Split out of 20_constraints.sql because their targets do not exist during
-- 04_index: the pipeline builds base tables first, indexes them, and only
-- then materializes the views that read from them.  Applying these here, at
-- the end of 06_derive, is the earliest point at which the targets exist.
--
-- Extracted from `pg_dump --section=post-data` on 2026-08-08.

CREATE UNIQUE INDEX IF NOT EXISTS idx_mfh_ein ON public.mv_org_financial_health USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mfh_health ON public.mv_org_financial_health USING btree (financial_health)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mfh_revenue ON public.mv_org_financial_health USING btree (avg_revenue DESC)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mfh_years ON public.mv_org_financial_health USING btree (years_of_data)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mnp_geom ON public.mv_nonprofit_profile USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_mnp_name_trgm ON public.mv_nonprofit_profile USING gin (org_name_current public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mnp_ntee ON public.mv_nonprofit_profile USING btree (ntee_irs)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mnp_revenue ON public.mv_nonprofit_profile USING btree (recent_revenue DESC)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mnp_revoked ON public.mv_nonprofit_profile USING btree (revocation_date)
  TABLESPACE ssd_1tb
  WHERE (revocation_date IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_mnp_state ON public.mv_nonprofit_profile USING btree (f990_org_addr_state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_mnp_subsection ON public.mv_nonprofit_profile USING btree (bmf_subsection_code)
  TABLESPACE ssd_1tb;
