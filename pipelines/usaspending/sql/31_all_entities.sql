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
    rgi.latitude::double precision,
    rgi.longitude::double precision,
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
