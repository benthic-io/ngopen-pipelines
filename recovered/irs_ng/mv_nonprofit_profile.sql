-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: irs_ng
-- object:   mv_nonprofit_profile
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_nonprofit_profile AS
WARNING:  database "irs_ng" has a collation version mismatch
DETAIL:  The database was created using collation version 2.42, but the operating system provides version 2.43.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE irs_ng REFRESH COLLATION VERSION, or build PostgreSQL with the right library version.
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
   FROM bmf_organizations b
     LEFT JOIN pub78_eligible p ON b.ein::text = p.ein::text
     LEFT JOIN revoked_organizations r ON b.ein::text = r.ein::text
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
           FROM form990_soi
          WHERE form990_soi.ein::text = b.ein::text
          ORDER BY form990_soi.tax_year DESC
         LIMIT 1) s ON true
  WHERE b.is_current = true
WITH NO DATA;
