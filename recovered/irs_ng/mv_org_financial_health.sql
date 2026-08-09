-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: irs_ng
-- object:   mv_org_financial_health
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_org_financial_health AS
 SELECT ein,
    count(*) AS years_of_data,
    min(tax_year) AS first_year,
    max(tax_year) AS latest_year,
    avg(total_revenue) AS avg_revenue,
    avg(total_expenses) AS avg_expenses,
    avg(
        CASE
            WHEN total_revenue > 0 THEN (total_revenue - total_expenses)::numeric / total_revenue::numeric * 100::numeric
            ELSE NULL::numeric
        END) AS avg_margin_pct,
    sum(contributions) AS total_contributions,
    sum(grants_paid) AS total_grants_paid,
    sum(compensation_officers) AS total_officer_comp,
    bool_or(filed_990t) AS ever_filed_990t,
    bool_or(lobbying_activities) AS ever_lobbied,
    bool_or(political_activities) AS ever_political,
    max(total_revenue) - min(total_revenue) AS revenue_change,
        CASE
            WHEN count(*) >= 3 AND avg(
            CASE
                WHEN total_revenue > 0 THEN (total_revenue - total_expenses)::numeric / total_revenue::numeric * 100::numeric
                ELSE NULL::numeric
            END) > 10::numeric THEN 'healthy'::text
            WHEN count(*) >= 3 AND avg(
            CASE
                WHEN total_revenue > 0 THEN (total_revenue - total_expenses)::numeric / total_revenue::numeric * 100::numeric
                ELSE NULL::numeric
            END) < 0::numeric THEN 'deficit'::text
            ELSE 'stable'::text
        END AS financial_health
   FROM form990_soi
  GROUP BY ein
 HAVING count(*) >= 2
WITH NO DATA;
