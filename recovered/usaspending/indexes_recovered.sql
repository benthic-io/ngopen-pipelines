-- RECOVERED INDEX DDL -- base relations
-- provenance: recovered
--
-- Indexes present in the live benthic.io database that are NOT created by any
-- known ETL script. Extracted verbatim from pg_indexes on 2026-08-08.
-- Constraint-backed indexes (*_pkey, *_key) are excluded: they are created
-- implicitly by their table definitions.
--
-- Applied in stage 04_index. Indexes whose target is a materialized view built
-- by stage 06_derive live in indexes_derived.sql instead -- they cannot be
-- created here because the relation does not exist yet.
--
-- Redundant pairs deliberately preserved for audit fidelity; see MIGRATION.md.


-- public.appropriation_account_balances
CREATE INDEX IF NOT EXISTS idx_aab_final_of_fy ON public.appropriation_account_balances USING btree (final_of_fy);
CREATE INDEX IF NOT EXISTS idx_aab_reporting_period_end ON public.appropriation_account_balances USING btree (reporting_period_end);
CREATE INDEX IF NOT EXISTS idx_aab_treasury_account_identifier ON public.appropriation_account_balances USING btree (treasury_account_identifier);

-- public.budget_authority
CREATE INDEX IF NOT EXISTS idx_ba_agency_year ON public.budget_authority USING btree (agency_identifier, year);

-- public.cgac
CREATE INDEX IF NOT EXISTS idx_cgac_code ON public.cgac USING btree (cgac_code);

-- public.disaster_emergency_fund_code
CREATE INDEX IF NOT EXISTS idx_defc_code ON public.disaster_emergency_fund_code USING btree (code);

-- public.federal_account
CREATE INDEX IF NOT EXISTS idx_fa_code ON public.federal_account USING btree (federal_account_code);
CREATE INDEX IF NOT EXISTS idx_fa_parent_agency ON public.federal_account USING btree (parent_toptier_agency_id);
CREATE INDEX IF NOT EXISTS idx_fa_title_trgm ON public.federal_account USING gin (account_title gin_trgm_ops);

-- public.financial_accounts_by_awards
CREATE INDEX IF NOT EXISTS idx_fabaward_disaster_emergency ON public.financial_accounts_by_awards USING btree (disaster_emergency_fund_code);
CREATE INDEX IF NOT EXISTS idx_fabaward_fain ON public.financial_accounts_by_awards USING btree (fain);
CREATE INDEX IF NOT EXISTS idx_fabaward_obligations ON public.financial_accounts_by_awards USING btree (obligations_incurred_total_by_award_cpe);
CREATE INDEX IF NOT EXISTS idx_fabaward_piid ON public.financial_accounts_by_awards USING btree (piid);
CREATE INDEX IF NOT EXISTS idx_fabaward_reporting_period_end ON public.financial_accounts_by_awards USING btree (reporting_period_end);
CREATE INDEX IF NOT EXISTS idx_fabaward_submission_id ON public.financial_accounts_by_awards USING btree (submission_id);
CREATE INDEX IF NOT EXISTS idx_fabaward_treasury_account_id ON public.financial_accounts_by_awards USING btree (treasury_account_id);

-- public.financial_accounts_by_program_activity_object_class
CREATE INDEX IF NOT EXISTS idx_fabpoc_disaster_emergency ON public.financial_accounts_by_program_activity_object_class USING btree (disaster_emergency_fund_code);
CREATE INDEX IF NOT EXISTS idx_fabpoc_submission_id ON public.financial_accounts_by_program_activity_object_class USING btree (submission_id);
CREATE INDEX IF NOT EXISTS idx_fabpoc_treasury_account_id ON public.financial_accounts_by_program_activity_object_class USING btree (treasury_account_id);

-- public.frec
CREATE INDEX IF NOT EXISTS idx_frec_code ON public.frec USING btree (frec_code);

-- public.historic_parent_duns
CREATE INDEX IF NOT EXISTS idx_hpd_duns ON public.historic_parent_duns USING btree (awardee_or_recipient_uniqu);
CREATE INDEX IF NOT EXISTS idx_hpd_parent_duns ON public.historic_parent_duns USING btree (ultimate_parent_unique_ide);
CREATE INDEX IF NOT EXISTS idx_hpd_year ON public.historic_parent_duns USING btree (year);

-- public.naics
CREATE INDEX IF NOT EXISTS idx_naics_code ON public.naics USING btree (code);
CREATE INDEX IF NOT EXISTS idx_naics_desc_trgm ON public.naics USING gin (description gin_trgm_ops);

-- public.office
CREATE INDEX IF NOT EXISTS idx_office_agency_code ON public.office USING btree (agency_code);
CREATE INDEX IF NOT EXISTS idx_office_code ON public.office USING btree (office_code);

-- public.psc
CREATE INDEX IF NOT EXISTS idx_psc_code ON public.psc USING btree (code);
CREATE INDEX IF NOT EXISTS idx_psc_desc_trgm ON public.psc USING gin (description gin_trgm_ops);

-- public.recipient_geocode_index
CREATE INDEX IF NOT EXISTS idx_geocode_geom_point ON public.recipient_geocode_index USING gist (geom_point);
CREATE INDEX IF NOT EXISTS idx_recipient_geocode_source ON public.recipient_geocode_index USING btree (source_id);
CREATE INDEX IF NOT EXISTS idx_rgi_source_id ON public.recipient_geocode_index USING btree (source_id);

-- public.ref_population_cong_district
CREATE INDEX IF NOT EXISTS idx_pop_cd_state ON public.ref_population_cong_district USING btree (state_code);

-- public.ref_population_county
CREATE INDEX IF NOT EXISTS idx_pop_county_state ON public.ref_population_county USING btree (state_code);

-- public.references_cfda
CREATE INDEX IF NOT EXISTS idx_cfda_program_number ON public.references_cfda USING btree (program_number);
CREATE INDEX IF NOT EXISTS idx_cfda_title_trgm ON public.references_cfda USING gin (program_title gin_trgm_ops);

-- public.state_data
CREATE INDEX IF NOT EXISTS idx_state_data_fips ON public.state_data USING btree (fips);

-- public.submission_attributes
CREATE INDEX IF NOT EXISTS idx_sa_reporting_fiscal_year ON public.submission_attributes USING btree (reporting_fiscal_year);
CREATE INDEX IF NOT EXISTS idx_sa_toptier_code ON public.submission_attributes USING btree (toptier_code);

-- public.toptier_agency
CREATE INDEX IF NOT EXISTS idx_tta_name_trgm ON public.toptier_agency USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_tta_toptier_code ON public.toptier_agency USING btree (toptier_code);

-- public.treasury_appropriation_account
CREATE INDEX IF NOT EXISTS idx_tas_awarding_agency ON public.treasury_appropriation_account USING btree (awarding_toptier_agency_id);
CREATE INDEX IF NOT EXISTS idx_tas_federal_account_id ON public.treasury_appropriation_account USING btree (federal_account_id);
CREATE INDEX IF NOT EXISTS idx_tas_funding_agency ON public.treasury_appropriation_account USING btree (funding_toptier_agency_id);
CREATE INDEX IF NOT EXISTS idx_tas_rendering_label ON public.treasury_appropriation_account USING btree (tas_rendering_label);

-- public.uei_crosswalk
CREATE INDEX IF NOT EXISTS idx_uei_duns ON public.uei_crosswalk USING btree (awardee_or_recipient_uniqu);
CREATE INDEX IF NOT EXISTS idx_uei_uei ON public.uei_crosswalk USING btree (uei);

-- public.uei_crosswalk_2021
CREATE INDEX IF NOT EXISTS idx_uei2021_duns ON public.uei_crosswalk_2021 USING btree (awardee_or_recipient_uniqu);
CREATE INDEX IF NOT EXISTS idx_uei2021_uei ON public.uei_crosswalk_2021 USING btree (uei);

-- rpt.award_search
CREATE INDEX IF NOT EXISTS idx_award_search_recipient_hash ON rpt.award_search USING btree (recipient_hash);
CREATE INDEX IF NOT EXISTS idx_rpt_award_parent ON rpt.award_search USING btree (parent_uei);
CREATE INDEX IF NOT EXISTS idx_rpt_award_recipient ON rpt.award_search USING btree (recipient_uei);

-- rpt.recipient_lookup
CREATE INDEX IF NOT EXISTS idx_recipient_lookup_geocode_system ON rpt.recipient_lookup USING btree (geocode_system) WHERE (geocode_system IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_rpt_recipient_lookup_uei ON rpt.recipient_lookup USING btree (uei);

-- rpt.subaward_search
CREATE INDEX IF NOT EXISTS idx_rpt_subaward_prime_uei ON rpt.subaward_search USING btree (awardee_or_recipient_uei);
CREATE INDEX IF NOT EXISTS idx_rpt_subaward_sub_parent_uei ON rpt.subaward_search USING btree (sub_ultimate_parent_uei);
CREATE INDEX IF NOT EXISTS idx_rpt_subaward_sub_uei ON rpt.subaward_search USING btree (sub_awardee_or_recipient_uei);

-- rpt.transaction_search_fabs
CREATE INDEX IF NOT EXISTS idx_fabs_uei ON rpt.transaction_search_fabs USING btree (recipient_uei);

-- rpt.transaction_search_fpds
CREATE INDEX IF NOT EXISTS idx_fpds_uei ON rpt.transaction_search_fpds USING btree (recipient_uei);
