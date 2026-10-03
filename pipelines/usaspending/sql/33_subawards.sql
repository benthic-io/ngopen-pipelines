-- Extracted verbatim from ngopen/build_entity_awards.py (SQL_SUBAWARDS)
-- Source commit: c4dd142  Extracted: 2026-08-08
DROP MATERIALIZED VIEW IF EXISTS public.subawards CASCADE;

CREATE MATERIALIZED VIEW public.subawards AS
SELECT 
    ss.broker_subaward_id AS subaward_id,
    ss.subaward_number,
    ss.unique_award_key,
    ss.award_piid_fain AS prime_award_piid_fain,
    ss.parent_award_id,
    ss.subaward_type,
    ss.report_type,
    ss.award_amount AS prime_award_amount,
    ss.subaward_amount,
    ss.action_date AS prime_action_date,
    ss.sub_action_date,
    ss.fy AS fiscal_year,
    ss.subaward_report_year,
    ss.subaward_report_month,
    ss.broker_created_at,
    ss.broker_updated_at,
    ss.date_submitted,
    ss.awardee_or_recipient_legal AS prime_recipient_name,
    ss.awardee_or_recipient_uniqu AS prime_recipient_duns,
    ss.awardee_or_recipient_uei AS prime_recipient_uei,
    ss.ultimate_parent_legal_enti AS prime_parent_name,
    ss.ultimate_parent_unique_ide AS prime_parent_duns,
    ss.ultimate_parent_uei AS prime_parent_uei,
    ss.dba_name AS prime_dba_name,
    ss.business_types AS prime_business_types,
    ss.legal_entity_country_code AS prime_country,
    ss.legal_entity_country_name AS prime_country_name,
    ss.legal_entity_state_code AS prime_state,
    ss.legal_entity_state_name AS prime_state_name,
    ss.legal_entity_city_name AS prime_city,
    ss.legal_entity_zip AS prime_zip,
    ss.legal_entity_congressional AS prime_congressional_district,
    ss.legal_entity_address_line1 AS prime_address_line1,
    ss.legal_entity_foreign_posta AS prime_foreign_postal,
    ss.sub_awardee_or_recipient_legal_raw AS sub_recipient_name,
    ss.sub_awardee_or_recipient_uniqu AS sub_recipient_duns,
    ss.sub_awardee_or_recipient_uei AS sub_recipient_uei,
    ss.sub_ultimate_parent_legal_enti_raw AS sub_parent_name,
    ss.sub_ultimate_parent_unique_ide AS sub_parent_duns,
    ss.sub_ultimate_parent_uei AS sub_parent_uei,
    ss.sub_dba_name,
    ss.sub_business_types,
    ss.sub_legal_entity_country_code_raw AS sub_country,
    ss.sub_legal_entity_country_name_raw AS sub_country_name,
    ss.sub_legal_entity_state_code AS sub_state,
    ss.sub_legal_entity_state_name AS sub_state_name,
    ss.sub_legal_entity_city_name AS sub_city,
    ss.sub_legal_entity_zip AS sub_zip,
    ss.sub_legal_entity_congressional_raw AS sub_congressional_district,
    ss.sub_legal_entity_address_line1 AS sub_address_line1,
    ss.sub_legal_entity_foreign_posta AS sub_foreign_postal,
    ss.place_of_perform_country_co AS pop_country,
    ss.place_of_perform_country_na AS pop_country_name,
    ss.place_of_perform_state_code AS pop_state,
    ss.place_of_perform_state_name AS pop_state_name,
    ss.place_of_perform_city_name AS pop_city,
    ss.place_of_performance_zip AS pop_zip,
    ss.place_of_perform_congressio AS pop_congressional_district,
    ss.place_of_perform_street AS pop_street,
    ss.sub_place_of_perform_country_co_raw AS sub_pop_country,
    ss.sub_place_of_perform_country_name AS sub_pop_country_name,
    ss.sub_place_of_perform_state_code AS sub_pop_state,
    ss.sub_place_of_perform_state_name AS sub_pop_state_name,
    ss.sub_place_of_perform_city_name AS sub_pop_city,
    ss.sub_place_of_performance_zip AS sub_pop_zip,
    ss.sub_place_of_perform_congressio_raw AS sub_pop_congressional_district,
    ss.sub_place_of_perform_street AS sub_pop_street,
    ss.awarding_agency_code,
    ss.awarding_agency_name,
    ss.awarding_sub_tier_agency_c AS awarding_subtier_code,
    ss.awarding_sub_tier_agency_n AS awarding_subtier_agency,
    ss.awarding_office_code,
    ss.awarding_office_name,
    ss.funding_agency_code,
    ss.funding_agency_name,
    ss.funding_sub_tier_agency_co AS funding_subtier_code,
    ss.funding_sub_tier_agency_na AS funding_subtier_agency,
    ss.funding_office_code,
    ss.funding_office_name,
    ss.naics AS prime_naics,
    ss.naics_description AS prime_naics_description,
    ss.sub_naics,
    ss.cfda_numbers,
    ss.cfda_titles,
    ss.sub_cfda_numbers,
    ss.award_description AS prime_award_description,
    ss.subaward_description,
    ss.sub_high_comp_officer1_full_na AS officer1_name,
    ss.sub_high_comp_officer1_amount AS officer1_amount,
    ss.sub_high_comp_officer2_full_na AS officer2_name,
    ss.sub_high_comp_officer2_amount AS officer2_amount,
    ss.sub_high_comp_officer3_full_na AS officer3_name,
    ss.sub_high_comp_officer3_amount AS officer3_amount,
    ss.sub_high_comp_officer4_full_na AS officer4_name,
    ss.sub_high_comp_officer4_amount AS officer4_amount,
    ss.sub_high_comp_officer5_full_na AS officer5_name,
    ss.sub_high_comp_officer5_amount AS officer5_amount,
    ss.prime_id,
    ss.internal_id,
    COALESCE(ae_uei.entity_id, ae_duns.entity_id) AS linked_sub_entity_id,
    CASE WHEN ae_uei.entity_id IS NOT NULL THEN 'uei' WHEN ae_duns.entity_id IS NOT NULL THEN 'duns' ELSE 'unlinked' END AS sub_link_method,
    COALESCE(ae_prime_uei.entity_id, ae_prime_duns.entity_id) AS linked_prime_entity_id,
    CASE WHEN ae_prime_uei.entity_id IS NOT NULL THEN 'uei' WHEN ae_prime_duns.entity_id IS NOT NULL THEN 'duns' ELSE 'unlinked' END AS prime_link_method
FROM rpt.subaward_search ss
LEFT JOIN public.all_entities ae_uei ON ss.sub_awardee_or_recipient_uei = ae_uei.uei
LEFT JOIN public.all_entities ae_duns ON ss.sub_awardee_or_recipient_uniqu = ae_duns.duns AND ae_uei.entity_id IS NULL
LEFT JOIN public.all_entities ae_prime_uei ON ss.awardee_or_recipient_uei = ae_prime_uei.uei
LEFT JOIN public.all_entities ae_prime_duns ON ss.awardee_or_recipient_uniqu = ae_prime_duns.duns AND ae_prime_uei.entity_id IS NULL;

CREATE UNIQUE INDEX idx_subawards_subaward_id ON public.subawards(subaward_id)
  TABLESPACE ssd_1tb;
CREATE INDEX idx_subawards_unique_award_key ON public.subawards(unique_award_key)
  TABLESPACE ssd_1tb;
CREATE INDEX idx_subawards_sub_action_date ON public.subawards(sub_action_date)
  TABLESPACE ssd_1tb;
CREATE INDEX idx_subawards_fiscal_year ON public.subawards(fiscal_year)
  TABLESPACE ssd_1tb;
CREATE INDEX idx_subawards_sub_recipient_uei ON public.subawards(sub_recipient_uei)
  TABLESPACE ssd_1tb
  WHERE sub_recipient_uei IS NOT NULL;
CREATE INDEX idx_subawards_linked_sub_entity ON public.subawards(linked_sub_entity_id)
  TABLESPACE ssd_1tb
  WHERE linked_sub_entity_id IS NOT NULL;
CREATE INDEX idx_subawards_subaward_amount ON public.subawards(subaward_amount)
  TABLESPACE ssd_1tb
  WHERE subaward_amount > 0;
CREATE INDEX idx_subawards_sub_state ON public.subawards(sub_state)
  TABLESPACE ssd_1tb
  WHERE sub_state IS NOT NULL;
