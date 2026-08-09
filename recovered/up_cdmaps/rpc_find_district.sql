-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: ucla_polysci_cdmaps
-- object:   rpc_find_district
-- kind:     function

CREATE OR REPLACE FUNCTION public.rpc_find_district(lat double precision, lon double precision, congress integer DEFAULT 118)
 RETURNS TABLE(district_id character varying, statename character varying, district integer, congress_number integer)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT district_id, statename, district, congress_number
  FROM congressional_districts
  WHERE congress_number = congress
    AND ST_Contains(geom, ST_Transform(ST_SetSRID(ST_Point(lon, lat), 4326), 3857))
  LIMIT 1;
$function$
