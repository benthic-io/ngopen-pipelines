-- Constraints and secondary indexes on base relations.
--
-- Extracted from `pg_dump --section=post-data` against the live benthic.io
-- database on 2026-08-08.  Primary keys and unique constraints are applied
-- earlier, in 15_keys.sql, because the ingest INSERTs need their arbiter
-- indexes to exist before the first ON CONFLICT fires.
--
-- Indexes whose target is a materialized view live in 25_derived_indexes.sql
-- and are applied in 06_derive, after the views they index have been created.

CREATE INDEX IF NOT EXISTS idx_527_ein ON public.political_orgs_527 USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_527_geo_mod2 ON public.political_orgs_527 USING btree (((id % 2)), id)
  TABLESPACE ssd_1tb
  WHERE ((latitude IS NULL) AND (address IS NOT NULL) AND ((address)::text <> ''::text));

CREATE INDEX IF NOT EXISTS idx_527_geo_mod3 ON public.political_orgs_527 USING btree (((id % 3)), id)
  TABLESPACE ssd_1tb
  WHERE ((latitude IS NULL) AND (address IS NOT NULL) AND ((address)::text <> ''::text));

CREATE INDEX IF NOT EXISTS idx_527_geom_point ON public.political_orgs_527 USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_527_name_trgm ON public.political_orgs_527 USING gin (org_name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_527_not_geo ON public.political_orgs_527 USING btree (id)
  TABLESPACE ssd_1tb
  WHERE ((latitude IS NULL) AND (address IS NOT NULL) AND ((address)::text <> ''::text));

CREATE INDEX IF NOT EXISTS idx_527_state ON public.political_orgs_527 USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990d_ein ON public.form990_details USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990d_period ON public.form990_details USING btree (tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990det_ein ON public.form990_details USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990det_ein_period ON public.form990_details USING btree (ein, tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990det_has_disregarded ON public.form990_details USING btree (has_disregarded_entity)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990det_has_related ON public.form990_details USING btree (has_related_entity)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990det_tax_period ON public.form990_details USING btree (tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990n_ein ON public.form990n_small_orgs USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990pf_ein ON public.form990_soi_private_foundation USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990pf_ein_year ON public.form990_soi_private_foundation USING btree (ein, tax_year)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990pf_tax_year ON public.form990_soi_private_foundation USING btree (tax_year)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990so_ein ON public.form990_schedule_o USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990so_ein_period ON public.form990_schedule_o USING btree (ein, tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990so_tax_period ON public.form990_schedule_o USING btree (tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_ein ON public.form990_soi USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_ein_year ON public.form990_soi USING btree (ein, tax_year)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_is_501c3 ON public.form990_soi USING btree (is_501c3)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_ntee ON public.form990_soi USING btree (ntee_code)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_revenue ON public.form990_soi USING btree (total_revenue)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_state ON public.form990_soi USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990soi_tax_year ON public.form990_soi USING btree (tax_year)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990t_ein ON public.form990t_details USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990td_ein ON public.form990t_details USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990td_ein_period ON public.form990t_details USING btree (ein, tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_990td_tax_period ON public.form990t_details USING btree (tax_period)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_current ON public.bmf_organizations USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_ein ON public.bmf_organizations USING btree (ein)
  TABLESPACE ssd_1tb;

-- Trigram over the street column, which is the one callers actually search with
-- ILIKE. The two trigram indexes below cover the name columns; the address was
-- the gap, so `f990_org_addr_street=ilike.PO+BOX+1306%` fell back to a Seq Scan
-- over 1.5GB and took 2.3-6.5s. 121 candidates now, 51ms. A btree cannot serve
-- this: the pattern is a case-insensitive prefix, and text_pattern_ops only
-- helps LIKE, not ILIKE.
CREATE INDEX IF NOT EXISTS idx_bmf_addr_street_trgm ON public.bmf_organizations USING gin (f990_org_addr_street public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_geo_mod2 ON public.bmf_organizations USING btree (((id % 2)), id)
  TABLESPACE ssd_1tb
  WHERE ((latitude IS NULL) AND (f990_org_addr_street IS NOT NULL) AND (f990_org_addr_street <> ''::text));

CREATE INDEX IF NOT EXISTS idx_bmf_geo_mod3 ON public.bmf_organizations USING btree (((id % 3)), id)
  TABLESPACE ssd_1tb
  WHERE ((latitude IS NULL) AND (f990_org_addr_street IS NOT NULL) AND (f990_org_addr_street <> ''::text));

CREATE INDEX IF NOT EXISTS idx_bmf_geocoded ON public.bmf_organizations USING btree (latitude)
  TABLESPACE ssd_1tb
  WHERE (latitude IS NOT NULL);

-- The index rpc_nonprofits_nearby actually needs. It wraps the predicate in
-- ST_Transform(geom_point, 3857), so the GiST index on the raw 4326 column
-- above cannot serve it -- the projection sits between the index and the
-- predicate, and every row was reprojected and tested in a filter: 2,259,215
-- rows removed, 109,201 buffers, 2931ms. Indexing the transformed expression
-- lets ST_DWithin use it: 31 buffers, 3.5ms, and a 5,965-row radius query in
-- 40ms. An expression index rather than a generated column, because adding a
-- STORED generated column rewrites the table under an ACCESS EXCLUSIVE lock.
CREATE INDEX IF NOT EXISTS idx_bmf_geom_3857 ON public.bmf_organizations USING gist (ST_Transform(geom_point, 3857))
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_geom_point ON public.bmf_organizations USING gist (geom_point)
  TABLESPACE ssd_1tb
  WHERE (geom_point IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_bmf_is_current ON public.bmf_organizations USING btree (is_current)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_name_sec_trgm ON public.bmf_organizations USING gin (org_name_sec public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_name_trgm ON public.bmf_organizations USING gin (org_name_current public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_not_geocoded ON public.bmf_organizations USING btree (id)
  TABLESPACE ssd_1tb
  WHERE ((latitude IS NULL) AND (f990_org_addr_street IS NOT NULL) AND (f990_org_addr_street <> ''::text));

CREATE INDEX IF NOT EXISTS idx_bmf_ntee ON public.bmf_organizations USING btree (ntee_irs)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_ntee_irs ON public.bmf_organizations USING btree (ntee_irs)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_snap_ein ON public.bmf_organization_snapshots USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_snap_ein_date ON public.bmf_organization_snapshots USING btree (ein, release_date)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_snap_release_date ON public.bmf_organization_snapshots USING btree (release_date)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_state ON public.bmf_organizations USING btree (f990_org_addr_state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_bmf_subsection ON public.bmf_organizations USING btree (bmf_subsection_code)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_census_geo_type ON public.census_demographics USING btree (geo_type)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_census_geoid ON public.census_demographics USING btree (geoid)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_census_geoid_year_type ON public.census_demographics USING btree (geoid, year, geo_type)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_census_year ON public.census_demographics USING btree (year)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_pf_ein ON public.form990_soi_private_foundation USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_pf_year ON public.form990_soi_private_foundation USING btree (tax_year)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_pub78_ein ON public.pub78_eligible USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_pub78_name_trgm ON public.pub78_eligible USING gin (org_name public.gin_trgm_ops)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_pub78_state ON public.pub78_eligible USING btree (state)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_revoked_date ON public.revoked_organizations USING btree (revocation_date)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_revoked_ein ON public.revoked_organizations USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_schedule_o_ein ON public.form990_schedule_o USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON public.bmf_organization_snapshots USING btree (release_date)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_snapshots_ein ON public.bmf_organization_snapshots USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_soi_ein ON public.form990_soi USING btree (ein)
  TABLESPACE ssd_1tb;

CREATE INDEX IF NOT EXISTS idx_soi_year ON public.form990_soi USING btree (tax_year)
  TABLESPACE ssd_1tb;
