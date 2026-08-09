# Audit snapshot: dropped `raw.*` relations

- database: `usaspending_db`
- captured: 2026-08-09
- reason: upstream pre-transform staging tables, superseded by their `rpt`
  counterparts. Read by no benthic ETL, referenced in no published
  documentation, not declared queryable in the BDP manifest, and
  re-fetchable from the upstream archive on any refresh.

This file is the structural record of what was removed. It exists so the
removal is auditable: anyone can compare it against a fresh `pg_restore`
listing of the upstream archive and confirm nothing benthic-authored was lost.

## `raw.source_procurement_transaction`

| property | value |
|---|---|
| owner | `otherdrums` |
| total size | 207 GB (221,987,364,864 bytes) |
| reltuples | 105,515,808 |
| columns | 309 |
| indexes | 0 |

### Columns

| # | name | type | nullable |
|---|---|---|---|
| 1 | `detached_award_procurement_id` | `integer` | no |
| 2 | `detached_award_proc_unique` | `text` | no |
| 3 | `a_76_fair_act_action` | `text` | yes |
| 4 | `a_76_fair_act_action_desc` | `text` | yes |
| 5 | `action_date` | `text` | yes |
| 6 | `action_type` | `text` | yes |
| 7 | `action_type_description` | `text` | yes |
| 8 | `additional_reporting` | `text` | yes |
| 9 | `agency_id` | `text` | yes |
| 10 | `annual_revenue` | `text` | yes |
| 11 | `award_description` | `text` | yes |
| 12 | `award_modification_amendme` | `text` | yes |
| 13 | `award_or_idv_flag` | `text` | yes |
| 14 | `awardee_or_recipient_legal` | `text` | yes |
| 15 | `awardee_or_recipient_uniqu` | `text` | yes |
| 16 | `awarding_agency_code` | `text` | yes |
| 17 | `awarding_agency_name` | `text` | yes |
| 18 | `awarding_office_code` | `text` | yes |
| 19 | `awarding_office_name` | `text` | yes |
| 20 | `awarding_sub_tier_agency_c` | `text` | yes |
| 21 | `awarding_sub_tier_agency_n` | `text` | yes |
| 22 | `base_and_all_options_value` | `text` | yes |
| 23 | `base_exercised_options_val` | `text` | yes |
| 24 | `business_categories` | `text[]` | yes |
| 25 | `cage_code` | `text` | yes |
| 26 | `clinger_cohen_act_pla_desc` | `text` | yes |
| 27 | `clinger_cohen_act_planning` | `text` | yes |
| 28 | `commercial_item_acqui_desc` | `text` | yes |
| 29 | `commercial_item_acquisitio` | `text` | yes |
| 30 | `commercial_item_test_desc` | `text` | yes |
| 31 | `commercial_item_test_progr` | `text` | yes |
| 32 | `consolidated_contract` | `text` | yes |
| 33 | `consolidated_contract_desc` | `text` | yes |
| 34 | `construction_wage_rat_desc` | `text` | yes |
| 35 | `construction_wage_rate_req` | `text` | yes |
| 36 | `contingency_humanitar_desc` | `text` | yes |
| 37 | `contingency_humanitarian_o` | `text` | yes |
| 38 | `contract_award_type` | `text` | yes |
| 39 | `contract_award_type_desc` | `text` | yes |
| 40 | `contract_bundling` | `text` | yes |
| 41 | `contract_bundling_descrip` | `text` | yes |
| 42 | `contract_financing` | `text` | yes |
| 43 | `contract_financing_descrip` | `text` | yes |
| 44 | `contracting_officers_desc` | `text` | yes |
| 45 | `contracting_officers_deter` | `text` | yes |
| 46 | `cost_accounting_stand_desc` | `text` | yes |
| 47 | `cost_accounting_standards` | `text` | yes |
| 48 | `cost_or_pricing_data` | `text` | yes |
| 49 | `cost_or_pricing_data_desc` | `text` | yes |
| 50 | `country_of_product_or_desc` | `text` | yes |
| 51 | `country_of_product_or_serv` | `text` | yes |
| 52 | `created_at` | `timestamp without time zone` | yes |
| 53 | `current_total_value_award` | `text` | yes |
| 54 | `division_name` | `text` | yes |
| 55 | `division_number_or_office` | `text` | yes |
| 56 | `dod_claimant_prog_cod_desc` | `text` | yes |
| 57 | `dod_claimant_program_code` | `text` | yes |
| 58 | `domestic_or_foreign_e_desc` | `text` | yes |
| 59 | `domestic_or_foreign_entity` | `text` | yes |
| 60 | `epa_designated_produc_desc` | `text` | yes |
| 61 | `epa_designated_product` | `text` | yes |
| 62 | `evaluated_preference` | `text` | yes |
| 63 | `evaluated_preference_desc` | `text` | yes |
| 64 | `extent_compete_description` | `text` | yes |
| 65 | `extent_competed` | `text` | yes |
| 66 | `fair_opportunity_limi_desc` | `text` | yes |
| 67 | `fair_opportunity_limited_s` | `text` | yes |
| 68 | `fed_biz_opps` | `text` | yes |
| 69 | `fed_biz_opps_description` | `text` | yes |
| 70 | `federal_action_obligation` | `numeric` | yes |
| 71 | `foreign_funding` | `text` | yes |
| 72 | `foreign_funding_desc` | `text` | yes |
| 73 | `funding_agency_code` | `text` | yes |
| 74 | `funding_agency_name` | `text` | yes |
| 75 | `funding_office_code` | `text` | yes |
| 76 | `funding_office_name` | `text` | yes |
| 77 | `funding_sub_tier_agency_co` | `text` | yes |
| 78 | `funding_sub_tier_agency_na` | `text` | yes |
| 79 | `government_furnished_desc` | `text` | yes |
| 80 | `government_furnished_prope` | `text` | yes |
| 81 | `high_comp_officer1_amount` | `text` | yes |
| 82 | `high_comp_officer1_full_na` | `text` | yes |
| 83 | `high_comp_officer2_amount` | `text` | yes |
| 84 | `high_comp_officer2_full_na` | `text` | yes |
| 85 | `high_comp_officer3_amount` | `text` | yes |
| 86 | `high_comp_officer3_full_na` | `text` | yes |
| 87 | `high_comp_officer4_amount` | `text` | yes |
| 88 | `high_comp_officer4_full_na` | `text` | yes |
| 89 | `high_comp_officer5_amount` | `text` | yes |
| 90 | `high_comp_officer5_full_na` | `text` | yes |
| 91 | `idv_type` | `text` | yes |
| 92 | `idv_type_description` | `text` | yes |
| 93 | `information_technolog_desc` | `text` | yes |
| 94 | `information_technology_com` | `text` | yes |
| 95 | `inherently_government_desc` | `text` | yes |
| 96 | `inherently_government_func` | `text` | yes |
| 97 | `initial_report_date` | `text` | yes |
| 98 | `interagency_contract_desc` | `text` | yes |
| 99 | `interagency_contracting_au` | `text` | yes |
| 100 | `labor_standards` | `text` | yes |
| 101 | `labor_standards_descrip` | `text` | yes |
| 102 | `last_modified` | `text` | yes |
| 103 | `legal_entity_address_line1` | `text` | yes |
| 104 | `legal_entity_address_line2` | `text` | yes |
| 105 | `legal_entity_address_line3` | `text` | yes |
| 106 | `legal_entity_city_name` | `text` | yes |
| 107 | `legal_entity_congressional` | `text` | yes |
| 108 | `legal_entity_country_code` | `text` | yes |
| 109 | `legal_entity_country_name` | `text` | yes |
| 110 | `legal_entity_county_code` | `text` | yes |
| 111 | `legal_entity_county_name` | `text` | yes |
| 112 | `legal_entity_state_code` | `text` | yes |
| 113 | `legal_entity_state_descrip` | `text` | yes |
| 114 | `legal_entity_zip4` | `text` | yes |
| 115 | `legal_entity_zip5` | `text` | yes |
| 116 | `legal_entity_zip_last4` | `text` | yes |
| 117 | `local_area_set_aside` | `text` | yes |
| 118 | `local_area_set_aside_desc` | `text` | yes |
| 119 | `major_program` | `text` | yes |
| 120 | `materials_supplies_article` | `text` | yes |
| 121 | `materials_supplies_descrip` | `text` | yes |
| 122 | `multi_year_contract` | `text` | yes |
| 123 | `multi_year_contract_desc` | `text` | yes |
| 124 | `multiple_or_single_aw_desc` | `text` | yes |
| 125 | `multiple_or_single_award_i` | `text` | yes |
| 126 | `naics` | `text` | yes |
| 127 | `naics_description` | `text` | yes |
| 128 | `national_interest_action` | `text` | yes |
| 129 | `national_interest_desc` | `text` | yes |
| 130 | `number_of_actions` | `text` | yes |
| 131 | `number_of_employees` | `text` | yes |
| 132 | `number_of_offers_received` | `text` | yes |
| 133 | `ordering_period_end_date` | `text` | yes |
| 134 | `organizational_type` | `text` | yes |
| 135 | `other_statutory_authority` | `text` | yes |
| 136 | `other_than_full_and_o_desc` | `text` | yes |
| 137 | `other_than_full_and_open_c` | `text` | yes |
| 138 | `parent_award_id` | `text` | yes |
| 139 | `performance_based_se_desc` | `text` | yes |
| 140 | `performance_based_service` | `text` | yes |
| 141 | `period_of_perf_potential_e` | `text` | yes |
| 142 | `period_of_performance_curr` | `text` | yes |
| 143 | `period_of_performance_star` | `text` | yes |
| 144 | `piid` | `text` | yes |
| 145 | `place_of_manufacture` | `text` | yes |
| 146 | `place_of_manufacture_desc` | `text` | yes |
| 147 | `place_of_perf_country_desc` | `text` | yes |
| 148 | `place_of_perfor_state_desc` | `text` | yes |
| 149 | `place_of_perform_city_name` | `text` | yes |
| 150 | `place_of_perform_country_c` | `text` | yes |
| 151 | `place_of_perform_country_n` | `text` | yes |
| 152 | `place_of_perform_county_co` | `text` | yes |
| 153 | `place_of_perform_county_na` | `text` | yes |
| 154 | `place_of_perform_state_nam` | `text` | yes |
| 155 | `place_of_perform_zip_last4` | `text` | yes |
| 156 | `place_of_performance_congr` | `text` | yes |
| 157 | `place_of_performance_locat` | `text` | yes |
| 158 | `place_of_performance_state` | `text` | yes |
| 159 | `place_of_performance_zip4a` | `text` | yes |
| 160 | `place_of_performance_zip5` | `text` | yes |
| 161 | `potential_total_value_awar` | `text` | yes |
| 162 | `price_evaluation_adjustmen` | `text` | yes |
| 163 | `product_or_service_co_desc` | `text` | yes |
| 164 | `product_or_service_code` | `text` | yes |
| 165 | `program_acronym` | `text` | yes |
| 166 | `program_system_or_equ_desc` | `text` | yes |
| 167 | `program_system_or_equipmen` | `text` | yes |
| 168 | `pulled_from` | `text` | yes |
| 169 | `purchase_card_as_paym_desc` | `text` | yes |
| 170 | `purchase_card_as_payment_m` | `text` | yes |
| 171 | `recovered_materials_s_desc` | `text` | yes |
| 172 | `recovered_materials_sustai` | `text` | yes |
| 173 | `referenced_idv_agency_desc` | `text` | yes |
| 174 | `referenced_idv_agency_iden` | `text` | yes |
| 175 | `referenced_idv_agency_name` | `text` | yes |
| 176 | `referenced_idv_modificatio` | `text` | yes |
| 177 | `referenced_idv_type` | `text` | yes |
| 178 | `referenced_idv_type_desc` | `text` | yes |
| 179 | `referenced_mult_or_si_desc` | `text` | yes |
| 180 | `referenced_mult_or_single` | `text` | yes |
| 181 | `research` | `text` | yes |
| 182 | `research_description` | `text` | yes |
| 183 | `sam_exception` | `text` | yes |
| 184 | `sam_exception_description` | `text` | yes |
| 185 | `sea_transportation` | `text` | yes |
| 186 | `sea_transportation_desc` | `text` | yes |
| 187 | `solicitation_date` | `text` | yes |
| 188 | `solicitation_identifier` | `text` | yes |
| 189 | `solicitation_procedur_desc` | `text` | yes |
| 190 | `solicitation_procedures` | `text` | yes |
| 191 | `subcontracting_plan` | `text` | yes |
| 192 | `subcontracting_plan_desc` | `text` | yes |
| 193 | `total_obligated_amount` | `text` | yes |
| 194 | `transaction_number` | `text` | yes |
| 195 | `type_of_contract_pric_desc` | `text` | yes |
| 196 | `type_of_contract_pricing` | `text` | yes |
| 197 | `type_of_idc` | `text` | yes |
| 198 | `type_of_idc_description` | `text` | yes |
| 199 | `type_set_aside` | `text` | yes |
| 200 | `type_set_aside_description` | `text` | yes |
| 201 | `ultimate_parent_legal_enti` | `text` | yes |
| 202 | `ultimate_parent_unique_ide` | `text` | yes |
| 203 | `undefinitized_action` | `text` | yes |
| 204 | `undefinitized_action_desc` | `text` | yes |
| 205 | `unique_award_key` | `text` | yes |
| 206 | `updated_at` | `timestamp without time zone` | yes |
| 207 | `vendor_alternate_name` | `text` | yes |
| 208 | `vendor_alternate_site_code` | `text` | yes |
| 209 | `vendor_doing_as_business_n` | `text` | yes |
| 210 | `vendor_enabled` | `text` | yes |
| 211 | `vendor_fax_number` | `text` | yes |
| 212 | `vendor_legal_org_name` | `text` | yes |
| 213 | `vendor_location_disabled_f` | `text` | yes |
| 214 | `vendor_phone_number` | `text` | yes |
| 215 | `vendor_site_code` | `text` | yes |
| 216 | `awardee_or_recipient_uei` | `text` | yes |
| 217 | `ultimate_parent_uei` | `text` | yes |
| 218 | `small_business_competitive` | `boolean` | yes |
| 219 | `city_local_government` | `boolean` | yes |
| 220 | `county_local_government` | `boolean` | yes |
| 221 | `inter_municipal_local_gove` | `boolean` | yes |
| 222 | `local_government_owned` | `boolean` | yes |
| 223 | `municipality_local_governm` | `boolean` | yes |
| 224 | `school_district_local_gove` | `boolean` | yes |
| 225 | `township_local_government` | `boolean` | yes |
| 226 | `us_state_government` | `boolean` | yes |
| 227 | `us_federal_government` | `boolean` | yes |
| 228 | `federal_agency` | `boolean` | yes |
| 229 | `federally_funded_research` | `boolean` | yes |
| 230 | `us_tribal_government` | `boolean` | yes |
| 231 | `foreign_government` | `boolean` | yes |
| 232 | `community_developed_corpor` | `boolean` | yes |
| 233 | `labor_surplus_area_firm` | `boolean` | yes |
| 234 | `corporate_entity_not_tax_e` | `boolean` | yes |
| 235 | `corporate_entity_tax_exemp` | `boolean` | yes |
| 236 | `partnership_or_limited_lia` | `boolean` | yes |
| 237 | `sole_proprietorship` | `boolean` | yes |
| 238 | `small_agricultural_coopera` | `boolean` | yes |
| 239 | `international_organization` | `boolean` | yes |
| 240 | `us_government_entity` | `boolean` | yes |
| 241 | `emerging_small_business` | `boolean` | yes |
| 242 | `c8a_program_participant` | `boolean` | yes |
| 243 | `sba_certified_8_a_joint_ve` | `boolean` | yes |
| 244 | `dot_certified_disadvantage` | `boolean` | yes |
| 245 | `self_certified_small_disad` | `boolean` | yes |
| 246 | `historically_underutilized` | `boolean` | yes |
| 247 | `small_disadvantaged_busine` | `boolean` | yes |
| 248 | `the_ability_one_program` | `boolean` | yes |
| 249 | `historically_black_college` | `boolean` | yes |
| 250 | `c1862_land_grant_college` | `boolean` | yes |
| 251 | `c1890_land_grant_college` | `boolean` | yes |
| 252 | `c1994_land_grant_college` | `boolean` | yes |
| 253 | `minority_institution` | `boolean` | yes |
| 254 | `private_university_or_coll` | `boolean` | yes |
| 255 | `school_of_forestry` | `boolean` | yes |
| 256 | `state_controlled_instituti` | `boolean` | yes |
| 257 | `tribal_college` | `boolean` | yes |
| 258 | `veterinary_college` | `boolean` | yes |
| 259 | `educational_institution` | `boolean` | yes |
| 260 | `alaskan_native_servicing_i` | `boolean` | yes |
| 261 | `community_development_corp` | `boolean` | yes |
| 262 | `native_hawaiian_servicing` | `boolean` | yes |
| 263 | `domestic_shelter` | `boolean` | yes |
| 264 | `manufacturer_of_goods` | `boolean` | yes |
| 265 | `hospital_flag` | `boolean` | yes |
| 266 | `veterinary_hospital` | `boolean` | yes |
| 267 | `hispanic_servicing_institu` | `boolean` | yes |
| 268 | `foundation` | `boolean` | yes |
| 269 | `woman_owned_business` | `boolean` | yes |
| 270 | `minority_owned_business` | `boolean` | yes |
| 271 | `women_owned_small_business` | `boolean` | yes |
| 272 | `economically_disadvantaged` | `boolean` | yes |
| 273 | `joint_venture_women_owned` | `boolean` | yes |
| 274 | `joint_venture_economically` | `boolean` | yes |
| 275 | `veteran_owned_business` | `boolean` | yes |
| 276 | `service_disabled_veteran_o` | `boolean` | yes |
| 277 | `contracts` | `boolean` | yes |
| 278 | `grants` | `boolean` | yes |
| 279 | `receives_contracts_and_gra` | `boolean` | yes |
| 280 | `airport_authority` | `boolean` | yes |
| 281 | `council_of_governments` | `boolean` | yes |
| 282 | `housing_authorities_public` | `boolean` | yes |
| 283 | `interstate_entity` | `boolean` | yes |
| 284 | `planning_commission` | `boolean` | yes |
| 285 | `port_authority` | `boolean` | yes |
| 286 | `transit_authority` | `boolean` | yes |
| 287 | `subchapter_s_corporation` | `boolean` | yes |
| 288 | `limited_liability_corporat` | `boolean` | yes |
| 289 | `foreign_owned_and_located` | `boolean` | yes |
| 290 | `american_indian_owned_busi` | `boolean` | yes |
| 291 | `alaskan_native_owned_corpo` | `boolean` | yes |
| 292 | `indian_tribe_federally_rec` | `boolean` | yes |
| 293 | `native_hawaiian_owned_busi` | `boolean` | yes |
| 294 | `tribally_owned_business` | `boolean` | yes |
| 295 | `asian_pacific_american_own` | `boolean` | yes |
| 296 | `black_american_owned_busin` | `boolean` | yes |
| 297 | `hispanic_american_owned_bu` | `boolean` | yes |
| 298 | `native_american_owned_busi` | `boolean` | yes |
| 299 | `subcontinent_asian_asian_i` | `boolean` | yes |
| 300 | `other_minority_owned_busin` | `boolean` | yes |
| 301 | `for_profit_organization` | `boolean` | yes |
| 302 | `nonprofit_organization` | `boolean` | yes |
| 303 | `other_not_for_profit_organ` | `boolean` | yes |
| 304 | `us_local_government` | `boolean` | yes |
| 305 | `entity_data_source` | `text` | yes |
| 306 | `sba_cert_econ_disadv_wosb` | `boolean` | yes |
| 307 | `sba_cert_women_own_small_bus` | `boolean` | yes |
| 308 | `ser_disabvet_own_bus_join_ven` | `boolean` | yes |
| 309 | `small_business_joint_venture` | `boolean` | yes |

## `raw.source_assistance_transaction`

| property | value |
|---|---|
| owner | `otherdrums` |
| total size | 112 GB (119,790,673,920 bytes) |
| reltuples | 127,013,696 |
| columns | 101 |
| indexes | 0 |

### Columns

| # | name | type | nullable |
|---|---|---|---|
| 1 | `published_fabs_id` | `integer` | no |
| 2 | `afa_generated_unique` | `text` | no |
| 3 | `action_date` | `text` | yes |
| 4 | `action_type` | `text` | yes |
| 5 | `action_type_description` | `text` | yes |
| 6 | `assistance_type` | `text` | yes |
| 7 | `assistance_type_desc` | `text` | yes |
| 8 | `award_description` | `text` | yes |
| 9 | `award_modification_amendme` | `text` | yes |
| 10 | `awardee_or_recipient_legal` | `text` | yes |
| 11 | `awardee_or_recipient_uniqu` | `text` | yes |
| 12 | `awarding_agency_code` | `text` | yes |
| 13 | `awarding_agency_name` | `text` | yes |
| 14 | `awarding_office_code` | `text` | yes |
| 15 | `awarding_office_name` | `text` | yes |
| 16 | `awarding_sub_tier_agency_c` | `text` | yes |
| 17 | `awarding_sub_tier_agency_n` | `text` | yes |
| 18 | `business_categories` | `text[]` | yes |
| 19 | `business_funds_ind_desc` | `text` | yes |
| 20 | `business_funds_indicator` | `text` | yes |
| 21 | `business_types` | `text` | yes |
| 22 | `business_types_desc` | `text` | yes |
| 23 | `assistance_listing_number` | `text` | yes |
| 24 | `assistance_listing_title` | `text` | yes |
| 25 | `correction_delete_ind_desc` | `text` | yes |
| 26 | `correction_delete_indicatr` | `text` | yes |
| 27 | `created_at` | `timestamp without time zone` | yes |
| 28 | `face_value_loan_guarantee` | `numeric` | yes |
| 29 | `fain` | `text` | yes |
| 30 | `federal_action_obligation` | `numeric` | yes |
| 31 | `fiscal_year_and_quarter_co` | `text` | yes |
| 32 | `funding_agency_code` | `text` | yes |
| 33 | `funding_agency_name` | `text` | yes |
| 34 | `funding_office_code` | `text` | yes |
| 35 | `funding_office_name` | `text` | yes |
| 36 | `funding_sub_tier_agency_co` | `text` | yes |
| 37 | `funding_sub_tier_agency_na` | `text` | yes |
| 38 | `high_comp_officer1_amount` | `text` | yes |
| 39 | `high_comp_officer1_full_na` | `text` | yes |
| 40 | `high_comp_officer2_amount` | `text` | yes |
| 41 | `high_comp_officer2_full_na` | `text` | yes |
| 42 | `high_comp_officer3_amount` | `text` | yes |
| 43 | `high_comp_officer3_full_na` | `text` | yes |
| 44 | `high_comp_officer4_amount` | `text` | yes |
| 45 | `high_comp_officer4_full_na` | `text` | yes |
| 46 | `high_comp_officer5_amount` | `text` | yes |
| 47 | `high_comp_officer5_full_na` | `text` | yes |
| 48 | `is_active` | `boolean` | no |
| 49 | `is_historical` | `boolean` | yes |
| 50 | `legal_entity_address_line1` | `text` | yes |
| 51 | `legal_entity_address_line2` | `text` | yes |
| 52 | `legal_entity_address_line3` | `text` | yes |
| 53 | `legal_entity_city_code` | `text` | yes |
| 54 | `legal_entity_city_name` | `text` | yes |
| 55 | `legal_entity_congressional` | `text` | yes |
| 56 | `legal_entity_country_code` | `text` | yes |
| 57 | `legal_entity_country_name` | `text` | yes |
| 58 | `legal_entity_county_code` | `text` | yes |
| 59 | `legal_entity_county_name` | `text` | yes |
| 60 | `legal_entity_foreign_city` | `text` | yes |
| 61 | `legal_entity_foreign_descr` | `text` | yes |
| 62 | `legal_entity_foreign_posta` | `text` | yes |
| 63 | `legal_entity_foreign_provi` | `text` | yes |
| 64 | `legal_entity_state_code` | `text` | yes |
| 65 | `legal_entity_state_name` | `text` | yes |
| 66 | `legal_entity_zip5` | `text` | yes |
| 67 | `legal_entity_zip_last4` | `text` | yes |
| 68 | `modified_at` | `timestamp without time zone` | yes |
| 69 | `non_federal_funding_amount` | `numeric` | yes |
| 70 | `original_loan_subsidy_cost` | `numeric` | yes |
| 71 | `period_of_performance_curr` | `text` | yes |
| 72 | `period_of_performance_star` | `text` | yes |
| 73 | `place_of_perfor_state_code` | `text` | yes |
| 74 | `place_of_perform_country_c` | `text` | yes |
| 75 | `place_of_perform_country_n` | `text` | yes |
| 76 | `place_of_perform_county_co` | `text` | yes |
| 77 | `place_of_perform_county_na` | `text` | yes |
| 78 | `place_of_perform_state_nam` | `text` | yes |
| 79 | `place_of_perform_zip_last4` | `text` | yes |
| 80 | `place_of_performance_city` | `text` | yes |
| 81 | `place_of_performance_code` | `text` | yes |
| 82 | `place_of_performance_congr` | `text` | yes |
| 83 | `place_of_performance_forei` | `text` | yes |
| 84 | `place_of_performance_zip4a` | `text` | yes |
| 85 | `place_of_performance_zip5` | `text` | yes |
| 86 | `place_of_performance_scope` | `text` | yes |
| 87 | `record_type` | `integer` | yes |
| 88 | `record_type_description` | `text` | yes |
| 89 | `sai_number` | `text` | yes |
| 90 | `submission_id` | `numeric` | yes |
| 91 | `total_funding_amount` | `text` | yes |
| 92 | `ultimate_parent_legal_enti` | `text` | yes |
| 93 | `ultimate_parent_unique_ide` | `text` | yes |
| 94 | `unique_award_key` | `text` | yes |
| 95 | `updated_at` | `timestamp without time zone` | yes |
| 96 | `uri` | `text` | yes |
| 97 | `uei` | `text` | yes |
| 98 | `ultimate_parent_uei` | `text` | yes |
| 99 | `funding_opportunity_goals` | `text` | yes |
| 100 | `funding_opportunity_number` | `text` | yes |
| 101 | `indirect_federal_sharing` | `numeric` | yes |

## `raw.source_assistance_transaction_backup`

| property | value |
|---|---|
| owner | `otherdrums` |
| total size | 107 GB (114,517,442,560 bytes) |
| reltuples | 123,725,256 |
| columns | 101 |
| indexes | 0 |

### Columns

| # | name | type | nullable |
|---|---|---|---|
| 1 | `published_fabs_id` | `integer` | yes |
| 2 | `afa_generated_unique` | `text` | yes |
| 3 | `action_date` | `text` | yes |
| 4 | `action_type` | `text` | yes |
| 5 | `action_type_description` | `text` | yes |
| 6 | `assistance_type` | `text` | yes |
| 7 | `assistance_type_desc` | `text` | yes |
| 8 | `award_description` | `text` | yes |
| 9 | `award_modification_amendme` | `text` | yes |
| 10 | `awardee_or_recipient_legal` | `text` | yes |
| 11 | `awardee_or_recipient_uniqu` | `text` | yes |
| 12 | `awarding_agency_code` | `text` | yes |
| 13 | `awarding_agency_name` | `text` | yes |
| 14 | `awarding_office_code` | `text` | yes |
| 15 | `awarding_office_name` | `text` | yes |
| 16 | `awarding_sub_tier_agency_c` | `text` | yes |
| 17 | `awarding_sub_tier_agency_n` | `text` | yes |
| 18 | `business_categories` | `text[]` | yes |
| 19 | `business_funds_ind_desc` | `text` | yes |
| 20 | `business_funds_indicator` | `text` | yes |
| 21 | `business_types` | `text` | yes |
| 22 | `business_types_desc` | `text` | yes |
| 23 | `assistance_listing_number` | `text` | yes |
| 24 | `assistance_listing_title` | `text` | yes |
| 25 | `correction_delete_ind_desc` | `text` | yes |
| 26 | `correction_delete_indicatr` | `text` | yes |
| 27 | `created_at` | `timestamp without time zone` | yes |
| 28 | `face_value_loan_guarantee` | `numeric` | yes |
| 29 | `fain` | `text` | yes |
| 30 | `federal_action_obligation` | `numeric` | yes |
| 31 | `fiscal_year_and_quarter_co` | `text` | yes |
| 32 | `funding_agency_code` | `text` | yes |
| 33 | `funding_agency_name` | `text` | yes |
| 34 | `funding_office_code` | `text` | yes |
| 35 | `funding_office_name` | `text` | yes |
| 36 | `funding_sub_tier_agency_co` | `text` | yes |
| 37 | `funding_sub_tier_agency_na` | `text` | yes |
| 38 | `high_comp_officer1_amount` | `text` | yes |
| 39 | `high_comp_officer1_full_na` | `text` | yes |
| 40 | `high_comp_officer2_amount` | `text` | yes |
| 41 | `high_comp_officer2_full_na` | `text` | yes |
| 42 | `high_comp_officer3_amount` | `text` | yes |
| 43 | `high_comp_officer3_full_na` | `text` | yes |
| 44 | `high_comp_officer4_amount` | `text` | yes |
| 45 | `high_comp_officer4_full_na` | `text` | yes |
| 46 | `high_comp_officer5_amount` | `text` | yes |
| 47 | `high_comp_officer5_full_na` | `text` | yes |
| 48 | `is_active` | `boolean` | yes |
| 49 | `is_historical` | `boolean` | yes |
| 50 | `legal_entity_address_line1` | `text` | yes |
| 51 | `legal_entity_address_line2` | `text` | yes |
| 52 | `legal_entity_address_line3` | `text` | yes |
| 53 | `legal_entity_city_code` | `text` | yes |
| 54 | `legal_entity_city_name` | `text` | yes |
| 55 | `legal_entity_congressional` | `text` | yes |
| 56 | `legal_entity_country_code` | `text` | yes |
| 57 | `legal_entity_country_name` | `text` | yes |
| 58 | `legal_entity_county_code` | `text` | yes |
| 59 | `legal_entity_county_name` | `text` | yes |
| 60 | `legal_entity_foreign_city` | `text` | yes |
| 61 | `legal_entity_foreign_descr` | `text` | yes |
| 62 | `legal_entity_foreign_posta` | `text` | yes |
| 63 | `legal_entity_foreign_provi` | `text` | yes |
| 64 | `legal_entity_state_code` | `text` | yes |
| 65 | `legal_entity_state_name` | `text` | yes |
| 66 | `legal_entity_zip5` | `text` | yes |
| 67 | `legal_entity_zip_last4` | `text` | yes |
| 68 | `modified_at` | `timestamp without time zone` | yes |
| 69 | `non_federal_funding_amount` | `numeric` | yes |
| 70 | `original_loan_subsidy_cost` | `numeric` | yes |
| 71 | `period_of_performance_curr` | `text` | yes |
| 72 | `period_of_performance_star` | `text` | yes |
| 73 | `place_of_perfor_state_code` | `text` | yes |
| 74 | `place_of_perform_country_c` | `text` | yes |
| 75 | `place_of_perform_country_n` | `text` | yes |
| 76 | `place_of_perform_county_co` | `text` | yes |
| 77 | `place_of_perform_county_na` | `text` | yes |
| 78 | `place_of_perform_state_nam` | `text` | yes |
| 79 | `place_of_perform_zip_last4` | `text` | yes |
| 80 | `place_of_performance_city` | `text` | yes |
| 81 | `place_of_performance_code` | `text` | yes |
| 82 | `place_of_performance_congr` | `text` | yes |
| 83 | `place_of_performance_forei` | `text` | yes |
| 84 | `place_of_performance_zip4a` | `text` | yes |
| 85 | `place_of_performance_zip5` | `text` | yes |
| 86 | `place_of_performance_scope` | `text` | yes |
| 87 | `record_type` | `integer` | yes |
| 88 | `record_type_description` | `text` | yes |
| 89 | `sai_number` | `text` | yes |
| 90 | `submission_id` | `numeric` | yes |
| 91 | `total_funding_amount` | `text` | yes |
| 92 | `ultimate_parent_legal_enti` | `text` | yes |
| 93 | `ultimate_parent_unique_ide` | `text` | yes |
| 94 | `unique_award_key` | `text` | yes |
| 95 | `updated_at` | `timestamp without time zone` | yes |
| 96 | `uri` | `text` | yes |
| 97 | `uei` | `text` | yes |
| 98 | `ultimate_parent_uei` | `text` | yes |
| 99 | `funding_opportunity_goals` | `text` | yes |
| 100 | `funding_opportunity_number` | `text` | yes |
| 101 | `indirect_federal_sharing` | `numeric` | yes |


---

## Execution record

Dropped 2026-08-09 on the live `usaspending_db`.

| | Before | After |
|---|---|---|
| `usaspending_db` size | 1138 GB | **713 GB** |
| `/raid_0` available | 1.1 T | **1.5 T** |
| tables in schema `raw` | 3 | 0 |

Pre-drop safety checks, all clear:

- No view, materialized view, or rule outside the three tables depended on schema `raw` (`pg_depend` / `pg_rewrite`).
- No inbound foreign keys referenced any `raw` relation (`pg_constraint`).
- No reference in any pipeline SQL, recovered DDL, site content, or `AGENTS.md`.

### PostgREST reachability

Checked at the same time: PostgREST exposes only the `public` schema. Its OpenAPI
document lists 387 paths and none of them are `rpt` relations; direct requests to
`/award_search` and `/transaction_search` return 404.

The `SELECT` grants held by `web_anon` on 15 `rpt` relations are therefore inert —
they confer no reachable capability. The manifest's `queryable: false` on every
`rpt`, `raw`, and `int` relation was already accurate, and no revocation was needed.

This also means promoting a lineage relation to queryable is not a grant change.
It requires surfacing it in `public`, which a plain view does at zero storage cost.
