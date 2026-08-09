-- Constraints and secondary indexes on base relations.
--
-- Extracted from `pg_dump --section=post-data` against the live benthic.io
-- database on 2026-08-08.  Primary keys and unique constraints are applied
-- earlier, in 15_keys.sql, because the ingest INSERTs need their arbiter
-- indexes to exist before the first ON CONFLICT fires.
--
-- Indexes whose target is a materialized view live in 25_derived_indexes.sql
-- and are applied in 06_derive, after the views they index have been created.

CREATE INDEX IF NOT EXISTS idx_527_ein ON public.political_orgs_527 USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_527_geo_mod2 ON public.political_orgs_527 USING btree (((id % 2)), id) WHERE ((latitude IS NULL) AND (address IS NOT NULL) AND ((address)::text <> ''::text));

CREATE INDEX IF NOT EXISTS idx_527_geo_mod3 ON public.political_orgs_527 USING btree (((id % 3)), id) WHERE ((latitude IS NULL) AND (address IS NOT NULL) AND ((address)::text <> ''::text));

CREATE INDEX IF NOT EXISTS idx_527_geom_point ON public.political_orgs_527 USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_527_name_trgm ON public.political_orgs_527 USING gin (org_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_527_not_geo ON public.political_orgs_527 USING btree (id) WHERE ((latitude IS NULL) AND (address IS NOT NULL) AND ((address)::text <> ''::text));

CREATE INDEX IF NOT EXISTS idx_527_state ON public.political_orgs_527 USING btree (state);

CREATE INDEX IF NOT EXISTS idx_990d_ein ON public.form990_details USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990d_period ON public.form990_details USING btree (tax_period);

CREATE INDEX IF NOT EXISTS idx_990det_ein ON public.form990_details USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990det_ein_period ON public.form990_details USING btree (ein, tax_period);

CREATE INDEX IF NOT EXISTS idx_990det_has_disregarded ON public.form990_details USING btree (has_disregarded_entity);

CREATE INDEX IF NOT EXISTS idx_990det_has_related ON public.form990_details USING btree (has_related_entity);

CREATE INDEX IF NOT EXISTS idx_990det_tax_period ON public.form990_details USING btree (tax_period);

CREATE INDEX IF NOT EXISTS idx_990n_ein ON public.form990n_small_orgs USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990pf_ein ON public.form990_soi_private_foundation USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990pf_ein_year ON public.form990_soi_private_foundation USING btree (ein, tax_year);

CREATE INDEX IF NOT EXISTS idx_990pf_tax_year ON public.form990_soi_private_foundation USING btree (tax_year);

CREATE INDEX IF NOT EXISTS idx_990so_ein ON public.form990_schedule_o USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990so_ein_period ON public.form990_schedule_o USING btree (ein, tax_period);

CREATE INDEX IF NOT EXISTS idx_990so_tax_period ON public.form990_schedule_o USING btree (tax_period);

CREATE INDEX IF NOT EXISTS idx_990soi_ein ON public.form990_soi USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990soi_ein_year ON public.form990_soi USING btree (ein, tax_year);

CREATE INDEX IF NOT EXISTS idx_990soi_is_501c3 ON public.form990_soi USING btree (is_501c3);

CREATE INDEX IF NOT EXISTS idx_990soi_ntee ON public.form990_soi USING btree (ntee_code);

CREATE INDEX IF NOT EXISTS idx_990soi_revenue ON public.form990_soi USING btree (total_revenue);

CREATE INDEX IF NOT EXISTS idx_990soi_state ON public.form990_soi USING btree (state);

CREATE INDEX IF NOT EXISTS idx_990soi_tax_year ON public.form990_soi USING btree (tax_year);

CREATE INDEX IF NOT EXISTS idx_990t_ein ON public.form990t_details USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990td_ein ON public.form990t_details USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_990td_ein_period ON public.form990t_details USING btree (ein, tax_period);

CREATE INDEX IF NOT EXISTS idx_990td_tax_period ON public.form990t_details USING btree (tax_period);

CREATE INDEX IF NOT EXISTS idx_bmf_current ON public.bmf_organizations USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_bmf_ein ON public.bmf_organizations USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_bmf_geo_mod2 ON public.bmf_organizations USING btree (((id % 2)), id) WHERE ((latitude IS NULL) AND (f990_org_addr_street IS NOT NULL) AND (f990_org_addr_street <> ''::text));

CREATE INDEX IF NOT EXISTS idx_bmf_geo_mod3 ON public.bmf_organizations USING btree (((id % 3)), id) WHERE ((latitude IS NULL) AND (f990_org_addr_street IS NOT NULL) AND (f990_org_addr_street <> ''::text));

CREATE INDEX IF NOT EXISTS idx_bmf_geocoded ON public.bmf_organizations USING btree (latitude) WHERE (latitude IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_bmf_geom_point ON public.bmf_organizations USING gist (geom_point) WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_bmf_is_current ON public.bmf_organizations USING btree (is_current);

CREATE INDEX IF NOT EXISTS idx_bmf_name_sec_trgm ON public.bmf_organizations USING gin (org_name_sec public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_bmf_name_trgm ON public.bmf_organizations USING gin (org_name_current public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_bmf_not_geocoded ON public.bmf_organizations USING btree (id) WHERE ((latitude IS NULL) AND (f990_org_addr_street IS NOT NULL) AND (f990_org_addr_street <> ''::text));

CREATE INDEX IF NOT EXISTS idx_bmf_ntee ON public.bmf_organizations USING btree (ntee_irs);

CREATE INDEX IF NOT EXISTS idx_bmf_ntee_irs ON public.bmf_organizations USING btree (ntee_irs);

CREATE INDEX IF NOT EXISTS idx_bmf_snap_ein ON public.bmf_organization_snapshots USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_bmf_snap_ein_date ON public.bmf_organization_snapshots USING btree (ein, release_date);

CREATE INDEX IF NOT EXISTS idx_bmf_snap_release_date ON public.bmf_organization_snapshots USING btree (release_date);

CREATE INDEX IF NOT EXISTS idx_bmf_state ON public.bmf_organizations USING btree (f990_org_addr_state);

CREATE INDEX IF NOT EXISTS idx_bmf_subsection ON public.bmf_organizations USING btree (bmf_subsection_code);

CREATE INDEX IF NOT EXISTS idx_census_geo_type ON public.census_demographics USING btree (geo_type);

CREATE INDEX IF NOT EXISTS idx_census_geoid ON public.census_demographics USING btree (geoid);

CREATE INDEX IF NOT EXISTS idx_census_geoid_year_type ON public.census_demographics USING btree (geoid, year, geo_type);

CREATE INDEX IF NOT EXISTS idx_census_year ON public.census_demographics USING btree (year);

CREATE INDEX IF NOT EXISTS idx_pf_ein ON public.form990_soi_private_foundation USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_pf_year ON public.form990_soi_private_foundation USING btree (tax_year);

CREATE INDEX IF NOT EXISTS idx_pub78_ein ON public.pub78_eligible USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_pub78_name_trgm ON public.pub78_eligible USING gin (org_name public.gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_pub78_state ON public.pub78_eligible USING btree (state);

CREATE INDEX IF NOT EXISTS idx_revoked_date ON public.revoked_organizations USING btree (revocation_date);

CREATE INDEX IF NOT EXISTS idx_revoked_ein ON public.revoked_organizations USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_schedule_o_ein ON public.form990_schedule_o USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON public.bmf_organization_snapshots USING btree (release_date);

CREATE INDEX IF NOT EXISTS idx_snapshots_ein ON public.bmf_organization_snapshots USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_soi_ein ON public.form990_soi USING btree (ein);

CREATE INDEX IF NOT EXISTS idx_soi_year ON public.form990_soi USING btree (tax_year);
