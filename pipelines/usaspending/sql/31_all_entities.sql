-- Extracted verbatim from ngopen/build_entity_awards.py (SQL_ALL_ENTITIES)
-- Source commit: c4dd142  Extracted: 2026-08-08
-- Drop existing. Order matters: all_entities depends on the staging tables,
-- so the matview must go first, then its inputs. Doing this at the top rather
-- than the bottom is what makes the file re-runnable; see the note at the end.
DROP MATERIALIZED VIEW IF EXISTS public.all_entities CASCADE;
DROP TABLE IF EXISTS _staging_award_agg CASCADE;
DROP TABLE IF EXISTS _staging_subaward_agg CASCADE;
DROP TABLE IF EXISTS _staging_subaward_entities CASCADE;

-- Stage 1: Award aggregation by recipient
CREATE TABLE _staging_award_agg AS
SELECT 
    recipient_hash,
    COUNT(DISTINCT award_id) AS award_count,
    SUM(total_obligation) AS total_obligation,
    MIN(action_date) AS date_first_award,
    MAX(action_date) AS date_last_award
FROM rpt.award_search
WHERE recipient_hash IS NOT NULL
GROUP BY recipient_hash;

CREATE INDEX idx_staging_award_agg_hash ON _staging_award_agg(recipient_hash);

-- Stage 2: Subaward aggregation by prime recipient
CREATE TABLE _staging_subaward_agg AS
SELECT 
    awardee_or_recipient_uei AS uei,
    COUNT(*) AS prime_subaward_count,
    SUM(subaward_amount) AS prime_subaward_amount
FROM rpt.subaward_search
WHERE awardee_or_recipient_uei IS NOT NULL
GROUP BY awardee_or_recipient_uei;

CREATE INDEX idx_staging_subaward_agg_uei ON _staging_subaward_agg(uei);

-- Stage 3: Subaward-only entities
CREATE TABLE _staging_subaward_entities AS
SELECT DISTINCT ON (sub_awardee_or_recipient_uei)
    sub_awardee_or_recipient_uei AS uei,
    sub_awardee_or_recipient_legal AS legal_business_name,
    sub_awardee_or_recipient_uniqu AS duns,
    sub_ultimate_parent_uei AS parent_uei,
    sub_legal_entity_address_line1 AS address_line_1,
    sub_legal_entity_city_name AS city,
    sub_legal_entity_state_code AS state,
    sub_legal_entity_zip5 AS zip5,
    sub_legal_entity_country_code AS country_code,
    sub_legal_entity_congressional AS congressional_district,
    COUNT(*) AS subaward_received_count,
    SUM(subaward_amount) AS subaward_received_amount
FROM rpt.subaward_search
WHERE sub_awardee_or_recipient_uei IS NOT NULL
  AND sub_awardee_or_recipient_uei NOT IN (
      SELECT uei FROM rpt.recipient_lookup WHERE uei IS NOT NULL
  )
GROUP BY sub_awardee_or_recipient_uei,
         sub_awardee_or_recipient_legal,
         sub_awardee_or_recipient_uniqu,
         sub_ultimate_parent_uei,
         sub_legal_entity_address_line1,
         sub_legal_entity_city_name,
         sub_legal_entity_state_code,
         sub_legal_entity_zip5,
         sub_legal_entity_country_code,
         sub_legal_entity_congressional;

-- Create all_entities materialized view
CREATE MATERIALIZED VIEW public.all_entities AS
SELECT 
    rl.id AS entity_id,
    'prime'::text AS entity_type,
    rl.recipient_hash,
    rl.legal_business_name,
    rl.duns,
    rl.uei,
    rl.parent_uei,
    rl.address_line_1,
    rl.address_line_2,
    rl.city,
    rl.state,
    rl.zip5,
    rl.zip4,
    rl.country_code,
    rl.congressional_district,
    -- Live public.all_entities carries these as bare numeric, not double
    -- precision: build_entity_awards.py (c4dd142) added a lossy cast that the
    -- production matview never had. numeric is canonical -- it preserves the
    -- full NUMERIC(10,8) geocode precision instead of truncating to a float.
    rgi.latitude,
    rgi.longitude,
    rgi.geom_point,
    CASE WHEN rgi.latitude IS NOT NULL THEN true ELSE false END AS is_geocoded,
    ST_GeoHash(rgi.geom_point, 6) AS geohash_6,
    COALESCE(aa.award_count, 0) AS award_count,
    COALESCE(aa.total_obligation, 0.00) AS total_obligation,
    aa.date_first_award,
    aa.date_last_award,
    COALESCE(sa.prime_subaward_count, 0) AS prime_subaward_count,
    COALESCE(sa.prime_subaward_amount, 0.00) AS prime_subaward_amount,
    0::bigint AS subaward_received_count,
    0.00::numeric AS subaward_received_amount
FROM rpt.recipient_lookup rl
LEFT JOIN public.recipient_geocode_index rgi ON rl.id = rgi.source_id
LEFT JOIN _staging_award_agg aa ON rl.recipient_hash = aa.recipient_hash
LEFT JOIN _staging_subaward_agg sa ON rl.uei = sa.uei

UNION ALL

SELECT 
    (-100000000000::bigint - ROW_NUMBER() OVER ()) AS entity_id,
    'subaward'::text AS entity_type,
    NULL::uuid AS recipient_hash,
    legal_business_name,
    duns,
    uei,
    parent_uei,
    address_line_1,
    NULL::text AS address_line_2,
    city,
    state,
    zip5,
    NULL::text AS zip4,
    country_code,
    congressional_district,
    NULL::numeric AS latitude,
    NULL::numeric AS longitude,
    NULL::geometry AS geom_point,
    false AS is_geocoded,
    NULL::text AS geohash_6,
    0::bigint AS award_count,
    0.00::numeric AS total_obligation,
    NULL::date AS date_first_award,
    NULL::date AS date_last_award,
    0::bigint AS prime_subaward_count,
    0.00::numeric AS prime_subaward_amount,
    subaward_received_count,
    subaward_received_amount
FROM _staging_subaward_entities;

-- Indexes
CREATE UNIQUE INDEX idx_all_entities_entity_id ON public.all_entities(entity_id);
CREATE INDEX idx_all_entities_uei ON public.all_entities(uei) WHERE uei IS NOT NULL;
CREATE INDEX idx_all_entities_entity_type ON public.all_entities(entity_type);
CREATE INDEX idx_all_entities_state ON public.all_entities(state) WHERE state IS NOT NULL;
CREATE INDEX idx_all_entities_is_geocoded ON public.all_entities(is_geocoded) WHERE is_geocoded = true;
CREATE INDEX idx_all_entities_geom_point ON public.all_entities USING GIST(geom_point) WHERE geom_point IS NOT NULL;
CREATE INDEX idx_all_entities_geohash_6 ON public.all_entities(geohash_6) WHERE geohash_6 IS NOT NULL;
CREATE INDEX idx_all_entities_total_obligation ON public.all_entities(total_obligation) WHERE total_obligation > 0;

-- Staging cleanup: DELIBERATELY REMOVED.
--
-- The original build_entity_awards.py ended with:
--     DROP TABLE IF EXISTS _staging_award_agg CASCADE;
--     DROP TABLE IF EXISTS _staging_subaward_agg CASCADE;
--     DROP TABLE IF EXISTS _staging_subaward_entities CASCADE;
--
-- public.all_entities is a materialized view that SELECTs from all three
-- staging tables, so it depends on them. CASCADE therefore does not merely
-- drop the staging tables -- it drops all_entities along with them, and with
-- it every downstream view that joins to all_entities.
--
-- This is why the three _staging_* tables are still present in the live
-- usaspending_db: the cleanup could never succeed without destroying its own
-- output, so the surviving state is always "staging tables present".
--
-- The staging tables are kept, matching live reality. They are lineage
-- intermediates, are not exposed through PostgREST, and are truncated and
-- rebuilt by the DROP ... IF EXISTS at the top of this file on every run.

-- The district geography that pairs with the state geography indexed above.
-- all_entities is the most-used relation in the catalogue (3,501 of 17,223 MCP
-- calls, 40% of traffic), and idx_all_entities_state exists while
-- congressional_district had no index at all.
--
-- Measured on production 2026-10-02, EXPLAIN without ANALYZE:
--
--   before  Limit (cost=0.00..4.86 rows=10)
--             ->  Seq Scan on all_entities (cost=0.00..682563.45 rows=1403332)
--                   Filter: (congressional_district = '03'::text)
--
--   after   Limit (cost=0.44..4.21 rows=10)
--             ->  Index Scan using idx_all_entities_district
--                   (cost=0.44..529675.33 rows=1403317)
--                   Index Cond: (congressional_district = '03'::text)
--
-- Partial, WHERE congressional_district IS NOT NULL, exactly mirroring
-- idx_all_entities_state above. 399,213 of 17,884,243 rows are NULL, so the
-- partial form is both smaller and consistent with what is already there. The
-- live index is 116 MB.
--
-- The factor is only ~1.3 for '03', and that is not the index failing: '03'
-- matches 1,416,153 of 17,884,243 rows, 7.92%, so an Index Scan that visits 1.4M
-- heap rows and a Seq Scan of a 3.5 GB matview are within 30% of each other. The
-- matched-selectivity comparator is idx_all_entities_state on state='CA', 2.16M
-- rows, costing 542,831.39 -- the same shape.
--
-- The win is available across the whole spread, and the spread is wide: district
-- counts run from 1 row to 1,628,461. Every one of them now has a seek instead of
-- a 3.5 GB scan.
--
-- TABLESPACE ssd_1tb: the eleven live indexes on this matview are all in ssd_1tb,
-- but none of the CREATE statements above pins a tablespace, so a rebuild from
-- this file would put every one of them back on default_tablespace, which is
-- empty. That drift predates this index; it is recorded rather than fixed here
-- because changing all ten existing statements is a separate change. This one is
-- pinned so it does not add to it.
--
-- Built CREATE INDEX CONCURRENTLY on the running server (16.8s). This file is the
-- rebuild path: it begins with DROP MATERIALIZED VIEW ... CASCADE, so there are
-- no concurrent readers and CONCURRENTLY could not run inside a transaction.
CREATE INDEX idx_all_entities_district ON public.all_entities(congressional_district)
  TABLESPACE ssd_1tb
  WHERE congressional_district IS NOT NULL;
