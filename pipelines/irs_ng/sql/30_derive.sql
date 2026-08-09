-- ============================================================================
-- irs_ng: derived objects -- views, materialized views, RPC functions
-- (stage 06_derive)
--
-- PROVENANCE: extracted from the live `irs_ng` catalog on 2026-08-08.
-- Several of these objects have NO source in the legacy ngopen scripts; they
-- were created by hand in psql and are recovered here so the pipeline is
-- reproducible. The per-object recovered/ files carry individual provenance
-- headers; this file is the ordered, runnable form.
--
-- Idempotent: CREATE FUNCTION -> CREATE OR REPLACE FUNCTION, materialized
-- views use IF NOT EXISTS and are populated by the stage's REFRESH.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.rpc_nonprofits_in_district(state_name text, district_num integer, congress integer DEFAULT 118) RETURNS TABLE(ein character varying, org_name text, ntee character varying, state character varying, subsection character varying, revenue bigint)
    LANGUAGE sql STABLE
    AS $$
  SELECT b.ein, b.org_name_current, b.ntee_irs, b.f990_org_addr_state, b.bmf_subsection_code,
    (SELECT total_revenue FROM form990_soi WHERE ein = b.ein ORDER BY tax_year DESC LIMIT 1)
  FROM bmf_organizations b
  WHERE b.is_current = true
    AND b.geom_point IS NOT NULL
    AND ST_Contains(
      (SELECT geom FROM dblink('dbname=ucla_polysci_cdmaps',
        'SELECT geom FROM congressional_districts WHERE statename = ' || quote_literal(state_name)
        || ' AND district = ' || district_num || ' AND congress_number = ' || congress || ' LIMIT 1'
      ) AS d(geom geometry)),
      ST_Transform(b.geom_point, 3857)
    );
$$;

CREATE OR REPLACE FUNCTION public.rpc_nonprofits_nearby(lat double precision, lon double precision, radius_meters double precision DEFAULT 10000) RETURNS TABLE(ein character varying, org_name text, ntee character varying, state character varying, distance_meters double precision)
    LANGUAGE sql STABLE
    AS $$
  SELECT b.ein, b.org_name_current, b.ntee_irs, b.f990_org_addr_state,
    ST_Distance(
      ST_Transform(b.geom_point, 3857),
      ST_Transform(ST_SetSRID(ST_Point(lon, lat), 4326), 3857)
    ) AS distance_meters
  FROM bmf_organizations b
  WHERE b.is_current = true
    AND b.geom_point IS NOT NULL
    AND ST_DWithin(
      ST_Transform(b.geom_point, 3857),
      ST_Transform(ST_SetSRID(ST_Point(lon, lat), 4326), 3857),
      radius_meters
    )
  ORDER BY distance_meters;
$$;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_nonprofit_profile AS
 SELECT b.ein,
    b.org_name_current,
    b.org_name_sec,
    b.ntee_irs,
    b.nccs_level_1,
    b.bmf_subsection_code,
    b.f990_org_addr_city,
    b.f990_org_addr_state,
    b.org_addr_full,
    b.latitude,
    b.longitude,
    b.geom_point,
    b.org_ruling_year,
    p.is_deductible AS pub78_eligible,
    r.revocation_date,
    r.revocation_reason,
    s.total_revenue AS recent_revenue,
    s.total_expenses AS recent_expenses,
    s.total_assets AS recent_assets,
    s.tax_year AS latest_tax_year,
    s.compensation_officers,
    s.num_employees
   FROM (((public.bmf_organizations b
     LEFT JOIN public.pub78_eligible p ON (((b.ein)::text = (p.ein)::text)))
     LEFT JOIN public.revoked_organizations r ON (((b.ein)::text = (r.ein)::text)))
     LEFT JOIN LATERAL ( SELECT form990_soi.id,
            form990_soi.ein,
            form990_soi.tax_year,
            form990_soi.org_name,
            form990_soi.state,
            form990_soi.ntee_code,
            form990_soi.asset_size,
            form990_soi.total_revenue,
            form990_soi.total_expenses,
            form990_soi.total_assets,
            form990_soi.total_liabilities,
            form990_soi.net_assets,
            form990_soi.contributions,
            form990_soi.grants_paid,
            form990_soi.compensation_officers,
            form990_soi.revenue_less_expenses,
            form990_soi.total_programs,
            form990_soi.source_file,
            form990_soi.form_type,
            form990_soi.subseccd,
            form990_soi.is_501c3,
            form990_soi.total_program_revenue,
            form990_soi.investment_income,
            form990_soi.royalty_income,
            form990_soi.net_rental_income,
            form990_soi.net_gains_losses,
            form990_soi.fundraising_income,
            form990_soi.gaming_income,
            form990_soi.tax_exempt_interest,
            form990_soi.legal_fees,
            form990_soi.accounting_fees,
            form990_soi.professional_fundraising,
            form990_soi.management_fees,
            form990_soi.investment_mgmt_fees,
            form990_soi.advertising,
            form990_soi.office_expenses,
            form990_soi.occupancy,
            form990_soi.travel,
            form990_soi.insurance,
            form990_soi.depreciation,
            form990_soi.interest_expense,
            form990_soi.other_salaries_wages,
            form990_soi.pension_contributions,
            form990_soi.employee_benefits,
            form990_soi.payroll_taxes,
            form990_soi.total_reportable_comp,
            form990_soi.total_estimated_comp,
            form990_soi.individuals_over_100k,
            form990_soi.land_buildings_equipment,
            form990_soi.investments_end,
            form990_soi.cash_end,
            form990_soi.num_employees,
            form990_soi.num_orgs,
            form990_soi.total_support,
            form990_soi.non_pf_reason,
            form990_soi.filed_990t,
            form990_soi.unrelated_business_income,
            form990_soi.foreign_offices,
            form990_soi.political_activities,
            form990_soi.lobbying_activities,
            form990_soi.operates_hospital,
            form990_soi.donor_advised_funds
           FROM public.form990_soi
          WHERE ((form990_soi.ein)::text = (b.ein)::text)
          ORDER BY form990_soi.tax_year DESC
         LIMIT 1) s ON (true))
  WHERE (b.is_current = true)
  WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_org_financial_health AS
 SELECT ein,
    count(*) AS years_of_data,
    min(tax_year) AS first_year,
    max(tax_year) AS latest_year,
    avg(total_revenue) AS avg_revenue,
    avg(total_expenses) AS avg_expenses,
    avg(
        CASE
            WHEN (total_revenue > 0) THEN ((((total_revenue - total_expenses))::numeric / (total_revenue)::numeric) * (100)::numeric)
            ELSE NULL::numeric
        END) AS avg_margin_pct,
    sum(contributions) AS total_contributions,
    sum(grants_paid) AS total_grants_paid,
    sum(compensation_officers) AS total_officer_comp,
    bool_or(filed_990t) AS ever_filed_990t,
    bool_or(lobbying_activities) AS ever_lobbied,
    bool_or(political_activities) AS ever_political,
    (max(total_revenue) - min(total_revenue)) AS revenue_change,
        CASE
            WHEN ((count(*) >= 3) AND (avg(
            CASE
                WHEN (total_revenue > 0) THEN ((((total_revenue - total_expenses))::numeric / (total_revenue)::numeric) * (100)::numeric)
                ELSE NULL::numeric
            END) > (10)::numeric)) THEN 'healthy'::text
            WHEN ((count(*) >= 3) AND (avg(
            CASE
                WHEN (total_revenue > 0) THEN ((((total_revenue - total_expenses))::numeric / (total_revenue)::numeric) * (100)::numeric)
                ELSE NULL::numeric
            END) < (0)::numeric)) THEN 'deficit'::text
            ELSE 'stable'::text
        END AS financial_health
   FROM public.form990_soi
  GROUP BY ein
 HAVING (count(*) >= 2)
  WITH NO DATA;

CREATE OR REPLACE VIEW public.v_org_financial_profile AS
 SELECT b.ein,
    b.org_name_current,
    b.f990_org_addr_state,
    b.ntee_irs,
    b.bmf_subsection_code,
    b.latitude,
    b.longitude,
    s.tax_year,
    s.form_type,
    s.total_revenue,
    s.total_expenses,
    s.total_assets,
    s.contributions,
    s.compensation_officers,
    s.grants_paid,
    s.investment_income,
    s.total_program_revenue,
    s.num_employees,
    s.filed_990t,
    s.unrelated_business_income
   FROM (public.bmf_organizations b
     LEFT JOIN public.form990_soi s ON (((b.ein)::text = (s.ein)::text)))
  WHERE (b.is_current = true);

CREATE OR REPLACE VIEW public.v_org_multi_year AS
 SELECT ein,
    tax_year,
    total_revenue,
    total_expenses,
    total_assets,
    (total_revenue - total_expenses) AS net_income,
        CASE
            WHEN (total_revenue > 0) THEN round(((((total_revenue - total_expenses))::numeric / (total_revenue)::numeric) * (100)::numeric), 1)
            ELSE NULL::numeric
        END AS margin_pct,
    contributions,
    grants_paid,
    compensation_officers
   FROM public.form990_soi
  WHERE ((ein)::text IN ( SELECT form990_soi_1.ein
           FROM public.form990_soi form990_soi_1
          GROUP BY form990_soi_1.ein
         HAVING (count(*) >= 2)))
  ORDER BY ein, tax_year;

CREATE OR REPLACE VIEW public.v_political_orgs AS
 SELECT p.ein,
    p.org_name AS political_name,
    p.filing_type,
    p.org_type,
    p.city,
    p.state,
    p.latitude,
    p.longitude,
    b.org_name_current AS bmf_name,
    b.f990_org_addr_state AS bmf_state
   FROM (public.political_orgs_527 p
     LEFT JOIN public.bmf_organizations b ON (((p.ein)::text = (b.ein)::text)));
