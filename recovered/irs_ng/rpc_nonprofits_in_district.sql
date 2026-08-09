-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: irs_ng
-- object:   rpc_nonprofits_in_district
-- kind:     function

CREATE OR REPLACE FUNCTION public.rpc_nonprofits_in_district(state_name text, district_num integer, congress integer DEFAULT 118)
 RETURNS TABLE(ein character varying, org_name text, ntee character varying, state character varying, subsection character varying, revenue bigint)
 LANGUAGE sql
 STABLE
AS $function$
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
$function$
