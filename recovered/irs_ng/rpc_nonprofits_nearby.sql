-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: irs_ng
-- object:   rpc_nonprofits_nearby
-- kind:     function

CREATE OR REPLACE FUNCTION public.rpc_nonprofits_nearby(lat double precision, lon double precision, radius_meters double precision DEFAULT 10000)
 RETURNS TABLE(ein character varying, org_name text, ntee character varying, state character varying, distance_meters double precision)
 LANGUAGE sql
 STABLE
AS $function$
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
$function$
