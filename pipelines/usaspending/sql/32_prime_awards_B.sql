-- Path B: aggregate rpt.transaction_search instead of reading rpt.award_search alone.
-- Upstream's "full" database download ships only ~354K rows in award_search while
-- transaction_search has 232M rows covering ~4.44M distinct awards.  The original
-- prime_awards was therefore missing ~4M awards the data actually contains.
--
-- This version groups transaction_search by award_id to discover every award,
-- falling back to award_search for the detail columns that transactions lack.
-- Awards present only in transactions carry NULL for those columns.
DROP MATERIALIZED VIEW IF EXISTS public.prime_awards CASCADE;

CREATE MATERIALIZED VIEW public.prime_awards AS
WITH distinct_awards AS (
    SELECT
        award_id,
        MAX(recipient_hash::text)::uuid AS recipient_hash,
        MAX(recipient_uei)     AS recipient_uei,
        MAX(recipient_name)    AS recipient_name,
        MAX(piid)              AS piid,
        MAX(fain)              AS fain,
        MAX(uri)               AS uri,
        MAX(naics_code)        AS naics_code,
        MAX(product_or_service_code) AS product_or_service_code,
        MAX(pop_state_code)    AS pop_state,
        MAX(type)              AS award_type,
        MIN(action_date)             AS action_date,
        MAX(fiscal_year)             AS fiscal_year,
        SUM(federal_action_obligation)::numeric(23,2) AS total_obligation,
        BOOL_OR(is_fpds)             AS is_fpds
    FROM rpt.transaction_search
    GROUP BY award_id
)
SELECT
    ae.entity_id                               AS linked_entity_id,
    'recipient_hash'                           AS link_method,
    da.award_id                                AS award_id,
    COALESCE(as_.generated_unique_award_id,
             da.award_id::text)                AS unique_award_id,
    COALESCE(as_.piid,           da.piid)      AS piid,
    COALESCE(as_.fain,           da.fain)      AS fain,
    COALESCE(as_.uri,            da.uri)       AS uri,
    as_.display_award_id,
    as_.category,
    COALESCE(as_.type,           da.award_type) AS award_type,
    as_.type_description,
    as_.award_amount,
    da.total_obligation                         AS total_obligation,
    as_.total_subsidy_cost,
    as_.total_loan_value,
    as_.total_outlays,
    as_.original_loan_subsidy_cost,
    as_.face_value_loan_guarantee,
    as_.base_and_all_options_value,
    as_.base_exercised_options_val,
    as_.non_federal_funding_amount,
    da.action_date,
    da.fiscal_year,
    as_.date_signed,
    as_.period_of_performance_start_date,
    as_.period_of_performance_current_end_date,
    as_.ordering_period_end_date,
    as_.last_modified_date::date AS last_modified_date,
    as_.certified_date,
    as_.create_date,
    as_.update_date,
    as_.recipient_hash,
    COALESCE(as_.recipient_name,
             da.recipient_name)                 AS recipient_name,
    as_.recipient_unique_id                     AS recipient_duns,
    COALESCE(as_.recipient_uei,
             da.recipient_uei)                  AS recipient_uei,
    as_.parent_recipient_unique_id              AS parent_duns,
    as_.parent_uei,
    as_.business_categories,
    as_.recipient_levels,
    as_.recipient_location_country_code          AS recipient_country,
    as_.recipient_location_country_name          AS recipient_country_name,
    as_.recipient_location_state_code            AS recipient_state,
    as_.recipient_location_state_name            AS recipient_state_name,
    as_.recipient_location_county_code           AS recipient_county_code,
    as_.recipient_location_county_name           AS recipient_county_name,
    as_.recipient_location_city_name             AS recipient_city,
    as_.recipient_location_zip5                  AS recipient_zip5,
    as_.recipient_location_congressional_code    AS recipient_congressional_district,
    as_.recipient_location_state_fips            AS recipient_state_fips,
    as_.pop_country_code                         AS pop_country,
    as_.pop_country_name                         AS pop_country_name,
    COALESCE(as_.pop_state_code,
             da.pop_state)                       AS pop_state,
    as_.pop_state_name                           AS pop_state_name,
    as_.pop_county_code                          AS pop_county_code,
    as_.pop_county_name                          AS pop_county_name,
    as_.pop_city_code                            AS pop_city_code,
    as_.pop_city_name                            AS pop_city,
    as_.pop_zip5                                 AS pop_zip5,
    as_.pop_congressional_code                   AS pop_congressional_district,
    as_.awarding_agency_id,
    as_.awarding_toptier_agency_name             AS awarding_agency,
    as_.awarding_toptier_agency_code             AS awarding_agency_code,
    as_.awarding_subtier_agency_name             AS awarding_subtier_agency,
    as_.awarding_subtier_agency_code             AS awarding_subtier_agency_code,
    as_.funding_agency_id,
    as_.funding_toptier_agency_name              AS funding_agency,
    as_.funding_toptier_agency_code              AS funding_agency_code,
    as_.funding_subtier_agency_name              AS funding_subtier_agency,
    as_.funding_subtier_agency_code              AS funding_subtier_agency_code,
    as_.cfda_program_title,
    as_.cfda_number,
    as_.cfdas,
    COALESCE(as_.naics_code,
             da.naics_code)                     AS naics_code,
    as_.naics_description,
    COALESCE(as_.product_or_service_code,
             da.product_or_service_code)        AS product_or_service_code,
    as_.product_or_service_description,
    as_.type_of_contract_pricing,
    as_.extent_competed,
    as_.type_set_aside,
    as_.sai_number,
    as_.description,
    as_.total_covid_outlay,
    as_.total_covid_obligation,
    as_.disaster_emergency_fund_codes,
    COALESCE(as_.is_fpds, da.is_fpds)           AS is_fpds,
    as_.total_obl_bin
FROM distinct_awards da
LEFT JOIN rpt.award_search as_
    ON da.award_id = as_.award_id
LEFT JOIN public.all_entities ae
    ON COALESCE(as_.recipient_hash, da.recipient_hash) = ae.recipient_hash;

CREATE UNIQUE INDEX IF NOT EXISTS idx_prime_awards_award_id ON public.prime_awards(award_id);
CREATE INDEX IF NOT EXISTS idx_prime_awards_linked_entity ON public.prime_awards(linked_entity_id);
CREATE INDEX IF NOT EXISTS idx_prime_awards_fiscal_year ON public.prime_awards(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_prime_awards_action_date ON public.prime_awards(action_date);
CREATE INDEX IF NOT EXISTS idx_prime_awards_recipient_uei ON public.prime_awards(recipient_uei);
CREATE INDEX IF NOT EXISTS idx_prime_awards_recipient_state ON public.prime_awards(recipient_state);
CREATE INDEX IF NOT EXISTS idx_prime_awards_pop_state ON public.prime_awards(pop_state);
CREATE INDEX IF NOT EXISTS idx_prime_awards_total_obligation ON public.prime_awards(total_obligation) WHERE total_obligation > 0;
CREATE INDEX IF NOT EXISTS idx_prime_awards_awarding_agency ON public.prime_awards(awarding_agency);

-- Composite of the two columns the site's own front end always pairs with the
-- sort. `awarding_agency_code` had no index at all, so a query filtering only on
-- it planned as a Seq Scan over 187 GB, and the filtered+sorted dashboard shape
-- read 153,228 buffers to return 20 rows -- 51s cold, 276ms warm. This seeks
-- straight to (agency, year) and walks total_obligation backwards: 24 buffers,
-- 0.06ms.
--
-- `total_obligation DESC` is last on purpose, so the same index serves a filter
-- with no sort at all. TABLESPACE is stated because the live copy lives on
-- ssd_1tb while every index above inherits default_tablespace, so without it a
-- rebuild quietly moves this 5.6GB index back to the RAID.
CREATE INDEX IF NOT EXISTS idx_prime_awards_agency_fy_total
  ON public.prime_awards(awarding_agency_code, fiscal_year, total_obligation DESC)
  TABLESPACE ssd_1tb;

-- Unfiltered top-N, which is what `order=total_obligation.desc&limit=5` sends.
-- Kept separate from idx_prime_awards_total_obligation because that one is ASC
-- and partial (`> 0`), so it cannot serve a descending order: btree reads `desc`
-- as `desc nulls first`, and a client asking for NULLS LAST therefore gets no
-- index at all and a parallel seq scan instead. That is a client-supplied query
-- string, so it is reachable from the public API -- measured at 310s before
-- this index existed.
CREATE INDEX IF NOT EXISTS idx_prime_awards_top
  ON public.prime_awards(total_obligation DESC)
  TABLESPACE ssd_1tb;

-- The filtered-and-sorted shape: fiscal_year equality plus an award_id sort.
-- The two single-column indexes cannot answer this together, and the planner
-- picked the worst available answer rather than a seq scan -- it walked the
-- whole 183M-entry idx_prime_awards_award_id and filtered fiscal_year on each
-- entry, estimated to touch 10,175,169 rows to return 100. Cost 0.57..112744059.
--
-- One such plan was orphaned by nginx at its 60s read timeout and kept burning
-- I/O in Postgres for 32 minutes before something terminated it. With this
-- index the same query seeks straight to the 2023 partition and reads the
-- award_id order for free, because award_id is the second column.
--
-- Cost fell 112,744,059 -> 30.84, a factor of ~3.66 million. Measured on
-- production 2026-09-30; EXPLAIN output in the benthic-publish repo under
-- task1/. TABLESPACE ssd_1tb for the same reason as the two above.
CREATE INDEX IF NOT EXISTS idx_prime_awards_fy_award_id
  ON public.prime_awards(fiscal_year, award_id)
  TABLESPACE ssd_1tb;

-- The district geography that pairs with the state geography indexed above.
-- idx_prime_awards_recipient_state and idx_prime_awards_pop_state were both
-- built; the congressional_district columns beside them never were, so the only
-- access path to a district filter was a scan of all 198 GB.
--
-- From the MCP's own trace store, prime_awards is 62% of all upstream time
-- (6,553s over 294 calls, 22,290ms average) on 1.7% of 17,223 calls, and
-- recipient_congressional_district was the filter on the largest single query on
-- record: one call, 3,731 MB read, 28.2 seconds.
--
-- Measured on production 2026-10-02, EXPLAIN without ANALYZE:
--
--   before  Limit (cost=0.00..17.06 rows=10)
--             ->  Seq Scan on prime_awards (cost=0.00..23815345.40 rows=13956439)
--                   Filter: (recipient_congressional_district = '03'::text)
--
--   after   Limit (cost=0.57..9.04 rows=10)
--             ->  Index Scan using idx_prime_awards_recipient_congressional_district
--                   (cost=0.57..11822827.99 rows=13962570)
--                   Index Cond: (recipient_congressional_district = '03'::text)
--
-- The scan cost fell by a factor of ~2.0. That is a smaller factor than it looks
-- because the filter is genuinely unselective: '03' matches 14,201,822 of
-- 182,995,664 rows, 7.76%. A Seq Scan and an Index Scan that has to visit 14M
-- heap rows are within a factor of two of each other -- the win is that the index
-- is free of the table's 198 GB of other columns, not that it visits few rows.
--
-- The fair comparison is the indexed column at the same selectivity:
-- recipient_state='CA' costs 0.57..11032157.49 for 12,648,309 rows. For matched
-- selectivity the two columns cost the same, which is the point: this index now
-- does exactly what the state index already did. Where the filter IS selective the
-- win is large -- recipient_state='03' costs 0.57..14763.74 for 17 rows, and
-- district values vary from 3.3M to 14.2M rows, so the same access path is
-- available at whatever selectivity a given district happens to have.
--
-- TABLESPACE ssd_1tb for the same reason as the three above: the table lives on
-- the SSD tablespace, so an unpinned build would put a 1.2 GB index on the RAID.
-- The live index is 1,209 MB.
--
-- Built CREATE INDEX CONCURRENTLY on the running server (20m51s). This file is the
-- rebuild path, where the matview was just dropped and recreated, where there are
-- no concurrent readers, and where CONCURRENTLY could not run inside a transaction
-- anyway.
CREATE INDEX IF NOT EXISTS idx_prime_awards_recipient_congressional_district
  ON public.prime_awards(recipient_congressional_district)
  TABLESPACE ssd_1tb;
