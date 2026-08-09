-- ============================================================================
-- up_cdmaps: derived objects -- views, materialized views, RPC functions
-- (stage 06_derive)
--
-- PROVENANCE: extracted from the live `ucla_polysci_cdmaps` catalog on 2026-08-08.
-- Several of these objects have NO source in the legacy ngopen scripts; they
-- were created by hand in psql and are recovered here so the pipeline is
-- reproducible. The per-object recovered/ files carry individual provenance
-- headers; this file is the ordered, runnable form.
--
-- Idempotent: CREATE FUNCTION -> CREATE OR REPLACE FUNCTION, materialized
-- views use IF NOT EXISTS and are populated by the stage's REFRESH.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.rpc_districts_in_bbox(min_lat double precision, max_lat double precision, min_lon double precision, max_lon double precision, congress integer DEFAULT 118) RETURNS TABLE(id integer, statename character varying, district integer, district_id character varying)
    LANGUAGE sql STABLE
    AS $$
  SELECT id, statename, district, district_id
  FROM congressional_districts
  WHERE congress_number = congress
    AND geom && ST_Transform(
      ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
      3857
    );
$$;

CREATE OR REPLACE FUNCTION public.rpc_find_district(lat double precision, lon double precision, congress integer DEFAULT 118) RETURNS TABLE(district_id character varying, statename character varying, district integer, congress_number integer)
    LANGUAGE sql STABLE
    AS $$
  SELECT district_id, statename, district, congress_number
  FROM congressional_districts
  WHERE congress_number = congress
    AND ST_Contains(geom, ST_Transform(ST_SetSRID(ST_Point(lon, lat), 4326), 3857))
  LIMIT 1;
$$;
