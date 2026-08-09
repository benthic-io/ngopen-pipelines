-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: ucla_polysci_cdmaps
-- object:   rpc_districts_in_bbox
-- kind:     function

CREATE OR REPLACE FUNCTION public.rpc_districts_in_bbox(min_lat double precision, max_lat double precision, min_lon double precision, max_lon double precision, congress integer DEFAULT 118)
 RETURNS TABLE(id integer, statename character varying, district integer, district_id character varying)
 LANGUAGE sql
 STABLE
AS $function$
  SELECT id, statename, district, district_id
  FROM congressional_districts
  WHERE congress_number = congress
    AND geom && ST_Transform(
      ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
      3857
    );
$function$
