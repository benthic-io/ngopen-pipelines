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
        SUM(federal_action_obligation) AS total_obligation,
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
    as_.last_modified_date,
    as_.certified_date,
    as_.create_date,
    as_.update_date,
    as_.recipient_hash                          AS recipient_hash_as,
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
