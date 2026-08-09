# usaspending

Generated 2026-08-09T15:20:26Z

| | |
|---|---|
| Reference (left) | `usaspending_db` |
| Candidate (right) | `usaspending_bdp_validate` |
| Schemas | `public` |

## Structural comparison

Structural equivalence is a gate. Every difference below is either a defect in the candidate pipeline or a change made by hand in the reference database that was never written back to source.

**Verdict: FAIL**

| Aspect | Only in reference | Only in candidate | Changed |
|---|---:|---:|---:|
| relations | 0 | 5 | 0 |
| columns | 0 | 36 | 7 |
| indexes | 2 | 2 | 0 |
| constraints | 0 | 27 | 0 |
| functions | 1 | 0 | 0 |
| grants | 554 | 520 | 0 |
| geometry | 0 | 0 | 0 |

### relations

**Only in `usaspending_bdp_validate`** (5)

- `public.ai_model`
- `public.message`
- `public.prompts`
- `public.session`
- `public.tool_use`

### columns

**Only in `usaspending_bdp_validate`** (36)

- `public.ai_model.id`
- `public.ai_model.model_id`
- `public.ai_model.name`
- `public.ai_model.provider`
- `public.gtas_sf133_balances.bea_category`
- `public.gtas_sf133_balances.budget_object_class`
- `public.gtas_sf133_balances.by_direct_reimbursable_fun`
- `public.gtas_sf133_balances.prior_year_adjustment`
- `public.gtas_sf133_balances.program_activity_reporting_key_code`
- `public.message.created_at`
- `public.message.id`
- `public.message.input_tokens`
- `public.message.latency`
- `public.message.message`
- `public.message.order`
- `public.message.output_tokens`
- `public.message.role`
- `public.message.session_id`
- `public.prompts.created_at`
- `public.prompts.description`
- `public.prompts.id`
- `public.prompts.name`
- `public.prompts.text`
- `public.session.ai_model_id`
- `public.session.ended_at`
- `public.session.feedback`
- `public.session.id`
- `public.session.started_at`
- `public.session.system_prompt_id`
- `public.session.tools`
- `public.tool_use.created_at`
- `public.tool_use.id`
- `public.tool_use.message_id`
- `public.tool_use.name`
- `public.tool_use.result`
- `public.tool_use.tool_input`

**Changed** (7)

- `public.all_entities.latitude`
  - reference: `numeric | NULL`
  - candidate: `double precision | NULL`
- `public.all_entities.longitude`
  - reference: `numeric | NULL`
  - candidate: `double precision | NULL`
- `public.mv_entity_spending_summary.latitude`
  - reference: `numeric | NULL`
  - candidate: `double precision | NULL`
- `public.mv_entity_spending_summary.longitude`
  - reference: `numeric | NULL`
  - candidate: `double precision | NULL`
- `public.prime_awards.last_modified_date`
  - reference: `date | NULL`
  - candidate: `timestamp with time zone | NULL`
- `public.recipient_geocode_index.latitude`
  - reference: `numeric(10,8) | NULL`
  - candidate: `numeric(10,7) | NULL`
- `public.recipient_geocode_index.longitude`
  - reference: `numeric(11,8) | NULL`
  - candidate: `numeric(11,7) | NULL`

### indexes

**Only in `usaspending_db`** (2)

- `public.financial_accounts_by_awards.idx_fabaward_distinct_award_key`
- `public.recipient_geocode_index.idx_rgi_geom_point`

**Only in `usaspending_bdp_validate`** (2)

- `public._staging_award_agg.idx_staging_award_agg_hash`
- `public._staging_subaward_agg.idx_staging_subaward_agg_uei`

### constraints

**Only in `usaspending_bdp_validate`** (27)

- `public.ai_model.ai_model_id_not_null`
- `public.ai_model.ai_model_model_id_not_null`
- `public.ai_model.ai_model_name_not_null`
- `public.ai_model.ai_model_provider_not_null`
- `public.message.message_created_at_not_null`
- `public.message.message_id_not_null`
- `public.message.message_input_tokens_not_null`
- `public.message.message_latency_not_null`
- `public.message.message_message_not_null`
- `public.message.message_order_not_null`
- `public.message.message_output_tokens_not_null`
- `public.message.message_role_not_null`
- `public.message.message_session_id_not_null`
- `public.prompts.prompts_created_at_not_null`
- `public.prompts.prompts_description_not_null`
- `public.prompts.prompts_id_not_null`
- `public.prompts.prompts_name_not_null`
- `public.prompts.prompts_text_not_null`
- `public.session.session_id_not_null`
- `public.session.session_started_at_not_null`
- `public.session.session_tools_not_null`
- `public.tool_use.tool_use_created_at_not_null`
- `public.tool_use.tool_use_id_not_null`
- `public.tool_use.tool_use_message_id_not_null`
- `public.tool_use.tool_use_name_not_null`
- `public.tool_use.tool_use_result_not_null`
- `public.tool_use.tool_use_tool_input_not_null`

### functions

**Only in `usaspending_db`** (1)

- `public.update_geom_point_trigger.`

### grants

**Only in `usaspending_db`** (554)

- `public._staging_award_agg.otherdrums.DELETE`
- `public._staging_award_agg.otherdrums.INSERT`
- `public._staging_award_agg.otherdrums.REFERENCES`
- `public._staging_award_agg.otherdrums.SELECT`
- `public._staging_award_agg.otherdrums.TRIGGER`
- `public._staging_award_agg.otherdrums.TRUNCATE`
- `public._staging_award_agg.otherdrums.UPDATE`
- `public._staging_award_agg.web_anon.SELECT`
- `public._staging_subaward_agg.otherdrums.DELETE`
- `public._staging_subaward_agg.otherdrums.INSERT`
- `public._staging_subaward_agg.otherdrums.REFERENCES`
- `public._staging_subaward_agg.otherdrums.SELECT`
- `public._staging_subaward_agg.otherdrums.TRIGGER`
- `public._staging_subaward_agg.otherdrums.TRUNCATE`
- `public._staging_subaward_agg.otherdrums.UPDATE`
- `public._staging_subaward_agg.web_anon.SELECT`
- `public._staging_subaward_entities.otherdrums.DELETE`
- `public._staging_subaward_entities.otherdrums.INSERT`
- `public._staging_subaward_entities.otherdrums.REFERENCES`
- `public._staging_subaward_entities.otherdrums.SELECT`
- `public._staging_subaward_entities.otherdrums.TRIGGER`
- `public._staging_subaward_entities.otherdrums.TRUNCATE`
- `public._staging_subaward_entities.otherdrums.UPDATE`
- `public._staging_subaward_entities.web_anon.SELECT`
- `public.agency.otherdrums.DELETE`
- `public.agency.otherdrums.INSERT`
- `public.agency.otherdrums.REFERENCES`
- `public.agency.otherdrums.SELECT`
- `public.agency.otherdrums.TRIGGER`
- `public.agency.otherdrums.TRUNCATE`
- `public.agency.otherdrums.UPDATE`
- `public.agency.web_anon.SELECT`
- `public.appropriation_account_balances.otherdrums.DELETE`
- `public.appropriation_account_balances.otherdrums.INSERT`
- `public.appropriation_account_balances.otherdrums.REFERENCES`
- `public.appropriation_account_balances.otherdrums.SELECT`
- `public.appropriation_account_balances.otherdrums.TRIGGER`
- `public.appropriation_account_balances.otherdrums.TRUNCATE`
- `public.appropriation_account_balances.otherdrums.UPDATE`
- `public.appropriation_account_balances.web_anon.SELECT`
- `public.auth_group.otherdrums.DELETE`
- `public.auth_group.otherdrums.INSERT`
- `public.auth_group.otherdrums.REFERENCES`
- `public.auth_group.otherdrums.SELECT`
- `public.auth_group.otherdrums.TRIGGER`
- `public.auth_group.otherdrums.TRUNCATE`
- `public.auth_group.otherdrums.UPDATE`
- `public.auth_group.web_anon.SELECT`
- `public.auth_group_permissions.otherdrums.DELETE`
- `public.auth_group_permissions.otherdrums.INSERT`
- `public.auth_group_permissions.otherdrums.REFERENCES`
- `public.auth_group_permissions.otherdrums.SELECT`
- `public.auth_group_permissions.otherdrums.TRIGGER`
- `public.auth_group_permissions.otherdrums.TRUNCATE`
- `public.auth_group_permissions.otherdrums.UPDATE`
- `public.auth_group_permissions.web_anon.SELECT`
- `public.auth_permission.otherdrums.DELETE`
- `public.auth_permission.otherdrums.INSERT`
- `public.auth_permission.otherdrums.REFERENCES`
- `public.auth_permission.otherdrums.SELECT`
- `public.auth_permission.otherdrums.TRIGGER`
- `public.auth_permission.otherdrums.TRUNCATE`
- `public.auth_permission.otherdrums.UPDATE`
- `public.auth_permission.web_anon.SELECT`
- `public.auth_user.otherdrums.DELETE`
- `public.auth_user.otherdrums.INSERT`
- `public.auth_user.otherdrums.REFERENCES`
- `public.auth_user.otherdrums.SELECT`
- `public.auth_user.otherdrums.TRIGGER`
- `public.auth_user.otherdrums.TRUNCATE`
- `public.auth_user.otherdrums.UPDATE`
- `public.auth_user.web_anon.SELECT`
- `public.auth_user_groups.otherdrums.DELETE`
- `public.auth_user_groups.otherdrums.INSERT`
- `public.auth_user_groups.otherdrums.REFERENCES`
- `public.auth_user_groups.otherdrums.SELECT`
- `public.auth_user_groups.otherdrums.TRIGGER`
- `public.auth_user_groups.otherdrums.TRUNCATE`
- `public.auth_user_groups.otherdrums.UPDATE`
- `public.auth_user_groups.web_anon.SELECT`
- `public.auth_user_user_permissions.otherdrums.DELETE`
- `public.auth_user_user_permissions.otherdrums.INSERT`
- `public.auth_user_user_permissions.otherdrums.REFERENCES`
- `public.auth_user_user_permissions.otherdrums.SELECT`
- `public.auth_user_user_permissions.otherdrums.TRIGGER`
- `public.auth_user_user_permissions.otherdrums.TRUNCATE`
- `public.auth_user_user_permissions.otherdrums.UPDATE`
- `public.auth_user_user_permissions.web_anon.SELECT`
- `public.award_category.otherdrums.DELETE`
- `public.award_category.otherdrums.INSERT`
- `public.award_category.otherdrums.REFERENCES`
- `public.award_category.otherdrums.SELECT`
- `public.award_category.otherdrums.TRIGGER`
- `public.award_category.otherdrums.TRUNCATE`
- `public.award_category.otherdrums.UPDATE`
- `public.award_category.web_anon.SELECT`
- `public.budget_authority.otherdrums.DELETE`
- `public.budget_authority.otherdrums.INSERT`
- `public.budget_authority.otherdrums.REFERENCES`
- `public.budget_authority.otherdrums.SELECT`
- `public.budget_authority.otherdrums.TRIGGER`
- `public.budget_authority.otherdrums.TRUNCATE`
- `public.budget_authority.otherdrums.UPDATE`
- `public.budget_authority.web_anon.SELECT`
- `public.bureau_title_lookup.otherdrums.DELETE`
- `public.bureau_title_lookup.otherdrums.INSERT`
- `public.bureau_title_lookup.otherdrums.REFERENCES`
- `public.bureau_title_lookup.otherdrums.SELECT`
- `public.bureau_title_lookup.otherdrums.TRIGGER`
- `public.bureau_title_lookup.otherdrums.TRUNCATE`
- `public.bureau_title_lookup.otherdrums.UPDATE`
- `public.bureau_title_lookup.web_anon.SELECT`
- `public.c_to_d_linkage_updates.otherdrums.DELETE`
- `public.c_to_d_linkage_updates.otherdrums.INSERT`
- `public.c_to_d_linkage_updates.otherdrums.REFERENCES`
- `public.c_to_d_linkage_updates.otherdrums.SELECT`
- `public.c_to_d_linkage_updates.otherdrums.TRIGGER`
- `public.c_to_d_linkage_updates.otherdrums.TRUNCATE`
- `public.c_to_d_linkage_updates.otherdrums.UPDATE`
- `public.c_to_d_linkage_updates.web_anon.SELECT`
- `public.cgac.otherdrums.DELETE`
- `public.cgac.otherdrums.INSERT`
- `public.cgac.otherdrums.REFERENCES`
- `public.cgac.otherdrums.SELECT`
- `public.cgac.otherdrums.TRIGGER`
- `public.cgac.otherdrums.TRUNCATE`
- `public.cgac.otherdrums.UPDATE`
- `public.cgac.web_anon.SELECT`
- `public.dabs_loader_queue.otherdrums.DELETE`
- `public.dabs_loader_queue.otherdrums.INSERT`
- `public.dabs_loader_queue.otherdrums.REFERENCES`
- `public.dabs_loader_queue.otherdrums.SELECT`
- `public.dabs_loader_queue.otherdrums.TRIGGER`
- `public.dabs_loader_queue.otherdrums.TRUNCATE`
- `public.dabs_loader_queue.otherdrums.UPDATE`
- `public.dabs_loader_queue.web_anon.SELECT`
- `public.dabs_submission_window_schedule.otherdrums.DELETE`
- `public.dabs_submission_window_schedule.otherdrums.INSERT`
- `public.dabs_submission_window_schedule.otherdrums.REFERENCES`
- `public.dabs_submission_window_schedule.otherdrums.SELECT`
- `public.dabs_submission_window_schedule.otherdrums.TRIGGER`
- `public.dabs_submission_window_schedule.otherdrums.TRUNCATE`
- `public.dabs_submission_window_schedule.otherdrums.UPDATE`
- `public.dabs_submission_window_schedule.web_anon.SELECT`
- `public.disaster_emergency_fund_code.otherdrums.DELETE`
- `public.disaster_emergency_fund_code.otherdrums.INSERT`
- `public.disaster_emergency_fund_code.otherdrums.REFERENCES`
- `public.disaster_emergency_fund_code.otherdrums.SELECT`
- `public.disaster_emergency_fund_code.otherdrums.TRIGGER`
- `public.disaster_emergency_fund_code.otherdrums.TRUNCATE`
- `public.disaster_emergency_fund_code.otherdrums.UPDATE`
- `public.disaster_emergency_fund_code.web_anon.SELECT`
- `public.django_admin_log.otherdrums.DELETE`
- `public.django_admin_log.otherdrums.INSERT`
- `public.django_admin_log.otherdrums.REFERENCES`
- `public.django_admin_log.otherdrums.SELECT`
- `public.django_admin_log.otherdrums.TRIGGER`
- `public.django_admin_log.otherdrums.TRUNCATE`
- `public.django_admin_log.otherdrums.UPDATE`
- `public.django_admin_log.web_anon.SELECT`
- `public.django_content_type.otherdrums.DELETE`
- `public.django_content_type.otherdrums.INSERT`
- `public.django_content_type.otherdrums.REFERENCES`
- `public.django_content_type.otherdrums.SELECT`
- `public.django_content_type.otherdrums.TRIGGER`
- `public.django_content_type.otherdrums.TRUNCATE`
- `public.django_content_type.otherdrums.UPDATE`
- `public.django_content_type.web_anon.SELECT`
- `public.django_migrations.otherdrums.DELETE`
- `public.django_migrations.otherdrums.INSERT`
- `public.django_migrations.otherdrums.REFERENCES`
- `public.django_migrations.otherdrums.SELECT`
- `public.django_migrations.otherdrums.TRIGGER`
- `public.django_migrations.otherdrums.TRUNCATE`
- `public.django_migrations.otherdrums.UPDATE`
- `public.django_migrations.web_anon.SELECT`
- `public.django_session.otherdrums.DELETE`
- `public.django_session.otherdrums.INSERT`
- `public.django_session.otherdrums.REFERENCES`
- `public.django_session.otherdrums.SELECT`
- `public.django_session.otherdrums.TRIGGER`
- `public.django_session.otherdrums.TRUNCATE`
- `public.django_session.otherdrums.UPDATE`
- `public.django_session.web_anon.SELECT`
- `public.download_job.otherdrums.DELETE`
- `public.download_job.otherdrums.INSERT`
- `public.download_job.otherdrums.REFERENCES`
- `public.download_job.otherdrums.SELECT`
- `public.download_job.otherdrums.TRIGGER`
- `public.download_job.otherdrums.TRUNCATE`
- `public.download_job.otherdrums.UPDATE`
- `public.download_job.web_anon.SELECT`
- `public.download_job_lookup.otherdrums.DELETE`
- `public.download_job_lookup.otherdrums.INSERT`
- `public.download_job_lookup.otherdrums.REFERENCES`
- `public.download_job_lookup.otherdrums.SELECT`
- `public.download_job_lookup.otherdrums.TRIGGER`
- `public.download_job_lookup.otherdrums.TRUNCATE`
- `public.download_job_lookup.otherdrums.UPDATE`
- `public.download_job_lookup.web_anon.SELECT`
- `public.external_data_load_date.otherdrums.DELETE`
- `public.external_data_load_date.otherdrums.INSERT`
- `public.external_data_load_date.otherdrums.REFERENCES`
- `public.external_data_load_date.otherdrums.SELECT`
- `public.external_data_load_date.otherdrums.TRIGGER`
- `public.external_data_load_date.otherdrums.TRUNCATE`
- `public.external_data_load_date.otherdrums.UPDATE`
- `public.external_data_load_date.web_anon.SELECT`
- `public.external_data_type.otherdrums.DELETE`
- `public.external_data_type.otherdrums.INSERT`
- `public.external_data_type.otherdrums.REFERENCES`
- `public.external_data_type.otherdrums.SELECT`
- `public.external_data_type.otherdrums.TRIGGER`
- `public.external_data_type.otherdrums.TRUNCATE`
- `public.external_data_type.otherdrums.UPDATE`
- `public.external_data_type.web_anon.SELECT`
- `public.federal_account.otherdrums.DELETE`
- `public.federal_account.otherdrums.INSERT`
- `public.federal_account.otherdrums.REFERENCES`
- `public.federal_account.otherdrums.SELECT`
- `public.federal_account.otherdrums.TRIGGER`
- `public.federal_account.otherdrums.TRUNCATE`
- `public.federal_account.otherdrums.UPDATE`
- `public.federal_account.web_anon.SELECT`
- `public.filter_hash.otherdrums.DELETE`
- `public.filter_hash.otherdrums.INSERT`
- `public.filter_hash.otherdrums.REFERENCES`
- `public.filter_hash.otherdrums.SELECT`
- `public.filter_hash.otherdrums.TRIGGER`
- `public.filter_hash.otherdrums.TRUNCATE`
- `public.filter_hash.otherdrums.UPDATE`
- `public.filter_hash.web_anon.SELECT`
- `public.financial_accounts_by_awards.otherdrums.DELETE`
- `public.financial_accounts_by_awards.otherdrums.INSERT`
- `public.financial_accounts_by_awards.otherdrums.REFERENCES`
- `public.financial_accounts_by_awards.otherdrums.SELECT`
- `public.financial_accounts_by_awards.otherdrums.TRIGGER`
- `public.financial_accounts_by_awards.otherdrums.TRUNCATE`
- `public.financial_accounts_by_awards.otherdrums.UPDATE`
- `public.financial_accounts_by_awards.web_anon.SELECT`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.DELETE`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.INSERT`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.REFERENCES`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.SELECT`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.TRIGGER`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.TRUNCATE`
- `public.financial_accounts_by_program_activity_object_class.otherdrums.UPDATE`
- `public.financial_accounts_by_program_activity_object_class.web_anon.SELECT`
- `public.frec.otherdrums.DELETE`
- `public.frec.otherdrums.INSERT`
- `public.frec.otherdrums.REFERENCES`
- `public.frec.otherdrums.SELECT`
- `public.frec.otherdrums.TRIGGER`
- `public.frec.otherdrums.TRUNCATE`
- `public.frec.otherdrums.UPDATE`
- `public.frec.web_anon.SELECT`
- `public.frec_map.otherdrums.DELETE`
- `public.frec_map.otherdrums.INSERT`
- `public.frec_map.otherdrums.REFERENCES`
- `public.frec_map.otherdrums.SELECT`
- `public.frec_map.otherdrums.TRIGGER`
- `public.frec_map.otherdrums.TRUNCATE`
- `public.frec_map.otherdrums.UPDATE`
- `public.frec_map.web_anon.SELECT`
- `public.geography_columns.web_anon.SELECT`
- `public.geometry_columns.web_anon.SELECT`
- `public.gtas_sf133_balances.otherdrums.DELETE`
- `public.gtas_sf133_balances.otherdrums.INSERT`
- `public.gtas_sf133_balances.otherdrums.REFERENCES`
- `public.gtas_sf133_balances.otherdrums.SELECT`
- `public.gtas_sf133_balances.otherdrums.TRIGGER`
- `public.gtas_sf133_balances.otherdrums.TRUNCATE`
- `public.gtas_sf133_balances.otherdrums.UPDATE`
- `public.gtas_sf133_balances.web_anon.SELECT`
- `public.historic_parent_duns.otherdrums.DELETE`
- `public.historic_parent_duns.otherdrums.INSERT`
- `public.historic_parent_duns.otherdrums.REFERENCES`
- `public.historic_parent_duns.otherdrums.SELECT`
- `public.historic_parent_duns.otherdrums.TRIGGER`
- `public.historic_parent_duns.otherdrums.TRUNCATE`
- `public.historic_parent_duns.otherdrums.UPDATE`
- `public.historic_parent_duns.web_anon.SELECT`
- `public.historical_appropriation_account_balances.otherdrums.DELETE`
- `public.historical_appropriation_account_balances.otherdrums.INSERT`
- `public.historical_appropriation_account_balances.otherdrums.REFERENCES`
- `public.historical_appropriation_account_balances.otherdrums.SELECT`
- `public.historical_appropriation_account_balances.otherdrums.TRIGGER`
- `public.historical_appropriation_account_balances.otherdrums.TRUNCATE`
- `public.historical_appropriation_account_balances.otherdrums.UPDATE`
- `public.historical_appropriation_account_balances.web_anon.SELECT`
- `public.job_status.otherdrums.DELETE`
- `public.job_status.otherdrums.INSERT`
- `public.job_status.otherdrums.REFERENCES`
- `public.job_status.otherdrums.SELECT`
- `public.job_status.otherdrums.TRIGGER`
- `public.job_status.otherdrums.TRUNCATE`
- `public.job_status.otherdrums.UPDATE`
- `public.job_status.web_anon.SELECT`
- `public.naics.otherdrums.DELETE`
- `public.naics.otherdrums.INSERT`
- `public.naics.otherdrums.REFERENCES`
- `public.naics.otherdrums.SELECT`
- `public.naics.otherdrums.TRIGGER`
- `public.naics.otherdrums.TRUNCATE`
- `public.naics.otherdrums.UPDATE`
- `public.naics.web_anon.SELECT`
- `public.object_class.otherdrums.DELETE`
- `public.object_class.otherdrums.INSERT`
- `public.object_class.otherdrums.REFERENCES`
- `public.object_class.otherdrums.SELECT`
- `public.object_class.otherdrums.TRIGGER`
- `public.object_class.otherdrums.TRUNCATE`
- `public.object_class.otherdrums.UPDATE`
- `public.object_class.web_anon.SELECT`
- `public.office.otherdrums.DELETE`
- `public.office.otherdrums.INSERT`
- `public.office.otherdrums.REFERENCES`
- `public.office.otherdrums.SELECT`
- `public.office.otherdrums.TRIGGER`
- `public.office.otherdrums.TRUNCATE`
- `public.office.otherdrums.UPDATE`
- `public.office.web_anon.SELECT`
- `public.overall_totals.otherdrums.DELETE`
- `public.overall_totals.otherdrums.INSERT`
- `public.overall_totals.otherdrums.REFERENCES`
- `public.overall_totals.otherdrums.SELECT`
- `public.overall_totals.otherdrums.TRIGGER`
- `public.overall_totals.otherdrums.TRUNCATE`
- `public.overall_totals.otherdrums.UPDATE`
- `public.overall_totals.web_anon.SELECT`
- `public.pg_stat_statements.otherdrums.DELETE`
- `public.pg_stat_statements.otherdrums.INSERT`
- `public.pg_stat_statements.otherdrums.REFERENCES`
- `public.pg_stat_statements.otherdrums.SELECT`
- `public.pg_stat_statements.otherdrums.TRIGGER`
- `public.pg_stat_statements.otherdrums.TRUNCATE`
- `public.pg_stat_statements.otherdrums.UPDATE`
- `public.pg_stat_statements.web_anon.SELECT`
- `public.pg_stat_statements_info.otherdrums.DELETE`
- `public.pg_stat_statements_info.otherdrums.INSERT`
- `public.pg_stat_statements_info.otherdrums.REFERENCES`
- `public.pg_stat_statements_info.otherdrums.SELECT`
- `public.pg_stat_statements_info.otherdrums.TRIGGER`
- `public.pg_stat_statements_info.otherdrums.TRUNCATE`
- `public.pg_stat_statements_info.otherdrums.UPDATE`
- `public.pg_stat_statements_info.web_anon.SELECT`
- `public.program_activity_park.otherdrums.DELETE`
- `public.program_activity_park.otherdrums.INSERT`
- `public.program_activity_park.otherdrums.REFERENCES`
- `public.program_activity_park.otherdrums.SELECT`
- `public.program_activity_park.otherdrums.TRIGGER`
- `public.program_activity_park.otherdrums.TRUNCATE`
- `public.program_activity_park.otherdrums.UPDATE`
- `public.program_activity_park.web_anon.SELECT`
- `public.psc.otherdrums.DELETE`
- `public.psc.otherdrums.INSERT`
- `public.psc.otherdrums.REFERENCES`
- `public.psc.otherdrums.SELECT`
- `public.psc.otherdrums.TRIGGER`
- `public.psc.otherdrums.TRUNCATE`
- `public.psc.otherdrums.UPDATE`
- `public.psc.web_anon.SELECT`
- `public.ref_city_county_state_code.otherdrums.DELETE`
- `public.ref_city_county_state_code.otherdrums.INSERT`
- `public.ref_city_county_state_code.otherdrums.REFERENCES`
- `public.ref_city_county_state_code.otherdrums.SELECT`
- `public.ref_city_county_state_code.otherdrums.TRIGGER`
- `public.ref_city_county_state_code.otherdrums.TRUNCATE`
- `public.ref_city_county_state_code.otherdrums.UPDATE`
- `public.ref_city_county_state_code.web_anon.SELECT`
- `public.ref_country_code.otherdrums.DELETE`
- `public.ref_country_code.otherdrums.INSERT`
- `public.ref_country_code.otherdrums.REFERENCES`
- `public.ref_country_code.otherdrums.SELECT`
- `public.ref_country_code.otherdrums.TRIGGER`
- `public.ref_country_code.otherdrums.TRUNCATE`
- `public.ref_country_code.otherdrums.UPDATE`
- `public.ref_country_code.web_anon.SELECT`
- `public.ref_population_cong_district.otherdrums.DELETE`
- `public.ref_population_cong_district.otherdrums.INSERT`
- `public.ref_population_cong_district.otherdrums.REFERENCES`
- `public.ref_population_cong_district.otherdrums.SELECT`
- `public.ref_population_cong_district.otherdrums.TRIGGER`
- `public.ref_population_cong_district.otherdrums.TRUNCATE`
- `public.ref_population_cong_district.otherdrums.UPDATE`
- `public.ref_population_cong_district.web_anon.SELECT`
- `public.ref_population_county.otherdrums.DELETE`
- `public.ref_population_county.otherdrums.INSERT`
- `public.ref_population_county.otherdrums.REFERENCES`
- `public.ref_population_county.otherdrums.SELECT`
- `public.ref_population_county.otherdrums.TRIGGER`
- `public.ref_population_county.otherdrums.TRUNCATE`
- `public.ref_population_county.otherdrums.UPDATE`
- `public.ref_population_county.web_anon.SELECT`
- `public.ref_program_activity.otherdrums.DELETE`
- `public.ref_program_activity.otherdrums.INSERT`
- `public.ref_program_activity.otherdrums.REFERENCES`
- `public.ref_program_activity.otherdrums.SELECT`
- `public.ref_program_activity.otherdrums.TRIGGER`
- `public.ref_program_activity.otherdrums.TRUNCATE`
- `public.ref_program_activity.otherdrums.UPDATE`
- `public.ref_program_activity.web_anon.SELECT`
- `public.references_cfda.otherdrums.DELETE`
- `public.references_cfda.otherdrums.INSERT`
- `public.references_cfda.otherdrums.REFERENCES`
- `public.references_cfda.otherdrums.SELECT`
- `public.references_cfda.otherdrums.TRIGGER`
- `public.references_cfda.otherdrums.TRUNCATE`
- `public.references_cfda.otherdrums.UPDATE`
- `public.references_cfda.web_anon.SELECT`
- `public.references_definition.otherdrums.DELETE`
- `public.references_definition.otherdrums.INSERT`
- `public.references_definition.otherdrums.REFERENCES`
- `public.references_definition.otherdrums.SELECT`
- `public.references_definition.otherdrums.TRIGGER`
- `public.references_definition.otherdrums.TRUNCATE`
- `public.references_definition.otherdrums.UPDATE`
- `public.references_definition.web_anon.SELECT`
- `public.reporting_agency_missing_tas.otherdrums.DELETE`
- `public.reporting_agency_missing_tas.otherdrums.INSERT`
- `public.reporting_agency_missing_tas.otherdrums.REFERENCES`
- `public.reporting_agency_missing_tas.otherdrums.SELECT`
- `public.reporting_agency_missing_tas.otherdrums.TRIGGER`
- `public.reporting_agency_missing_tas.otherdrums.TRUNCATE`
- `public.reporting_agency_missing_tas.otherdrums.UPDATE`
- `public.reporting_agency_missing_tas.web_anon.SELECT`
- `public.reporting_agency_overview.otherdrums.DELETE`
- `public.reporting_agency_overview.otherdrums.INSERT`
- `public.reporting_agency_overview.otherdrums.REFERENCES`
- `public.reporting_agency_overview.otherdrums.SELECT`
- `public.reporting_agency_overview.otherdrums.TRIGGER`
- `public.reporting_agency_overview.otherdrums.TRUNCATE`
- `public.reporting_agency_overview.otherdrums.UPDATE`
- `public.reporting_agency_overview.web_anon.SELECT`
- `public.reporting_agency_tas.otherdrums.DELETE`
- `public.reporting_agency_tas.otherdrums.INSERT`
- `public.reporting_agency_tas.otherdrums.REFERENCES`
- `public.reporting_agency_tas.otherdrums.SELECT`
- `public.reporting_agency_tas.otherdrums.TRIGGER`
- `public.reporting_agency_tas.otherdrums.TRUNCATE`
- `public.reporting_agency_tas.otherdrums.UPDATE`
- `public.reporting_agency_tas.web_anon.SELECT`
- `public.rest_framework_tracking_apirequestlog.otherdrums.DELETE`
- `public.rest_framework_tracking_apirequestlog.otherdrums.INSERT`
- `public.rest_framework_tracking_apirequestlog.otherdrums.REFERENCES`
- `public.rest_framework_tracking_apirequestlog.otherdrums.SELECT`
- `public.rest_framework_tracking_apirequestlog.otherdrums.TRIGGER`
- `public.rest_framework_tracking_apirequestlog.otherdrums.TRUNCATE`
- `public.rest_framework_tracking_apirequestlog.otherdrums.UPDATE`
- `public.rest_framework_tracking_apirequestlog.web_anon.SELECT`
- `public.rosetta.otherdrums.DELETE`
- `public.rosetta.otherdrums.INSERT`
- `public.rosetta.otherdrums.REFERENCES`
- `public.rosetta.otherdrums.SELECT`
- `public.rosetta.otherdrums.TRIGGER`
- `public.rosetta.otherdrums.TRUNCATE`
- `public.rosetta.otherdrums.UPDATE`
- `public.rosetta.web_anon.SELECT`
- `public.spatial_ref_sys.web_anon.SELECT`
- `public.state_data.otherdrums.DELETE`
- `public.state_data.otherdrums.INSERT`
- `public.state_data.otherdrums.REFERENCES`
- `public.state_data.otherdrums.SELECT`
- `public.state_data.otherdrums.TRIGGER`
- `public.state_data.otherdrums.TRUNCATE`
- `public.state_data.otherdrums.UPDATE`
- `public.state_data.web_anon.SELECT`
- `public.submission_attributes.otherdrums.DELETE`
- `public.submission_attributes.otherdrums.INSERT`
- `public.submission_attributes.otherdrums.REFERENCES`
- `public.submission_attributes.otherdrums.SELECT`
- `public.submission_attributes.otherdrums.TRIGGER`
- `public.submission_attributes.otherdrums.TRUNCATE`
- `public.submission_attributes.otherdrums.UPDATE`
- `public.submission_attributes.web_anon.SELECT`
- `public.subtier_agency.otherdrums.DELETE`
- `public.subtier_agency.otherdrums.INSERT`
- `public.subtier_agency.otherdrums.REFERENCES`
- `public.subtier_agency.otherdrums.SELECT`
- `public.subtier_agency.otherdrums.TRIGGER`
- `public.subtier_agency.otherdrums.TRUNCATE`
- `public.subtier_agency.otherdrums.UPDATE`
- `public.subtier_agency.web_anon.SELECT`
- `public.toptier_agency.otherdrums.DELETE`
- `public.toptier_agency.otherdrums.INSERT`
- `public.toptier_agency.otherdrums.REFERENCES`
- `public.toptier_agency.otherdrums.SELECT`
- `public.toptier_agency.otherdrums.TRIGGER`
- `public.toptier_agency.otherdrums.TRUNCATE`
- `public.toptier_agency.otherdrums.UPDATE`
- `public.toptier_agency.web_anon.SELECT`
- `public.treasury_appropriation_account.otherdrums.DELETE`
- `public.treasury_appropriation_account.otherdrums.INSERT`
- `public.treasury_appropriation_account.otherdrums.REFERENCES`
- `public.treasury_appropriation_account.otherdrums.SELECT`
- `public.treasury_appropriation_account.otherdrums.TRIGGER`
- `public.treasury_appropriation_account.otherdrums.TRUNCATE`
- `public.treasury_appropriation_account.otherdrums.UPDATE`
- `public.treasury_appropriation_account.web_anon.SELECT`
- `public.uei_crosswalk.otherdrums.DELETE`
- `public.uei_crosswalk.otherdrums.INSERT`
- `public.uei_crosswalk.otherdrums.REFERENCES`
- `public.uei_crosswalk.otherdrums.SELECT`
- `public.uei_crosswalk.otherdrums.TRIGGER`
- `public.uei_crosswalk.otherdrums.TRUNCATE`
- `public.uei_crosswalk.otherdrums.UPDATE`
- `public.uei_crosswalk_2021.otherdrums.DELETE`
- `public.uei_crosswalk_2021.otherdrums.INSERT`
- `public.uei_crosswalk_2021.otherdrums.REFERENCES`
- `public.uei_crosswalk_2021.otherdrums.SELECT`
- `public.uei_crosswalk_2021.otherdrums.TRIGGER`
- `public.uei_crosswalk_2021.otherdrums.TRUNCATE`
- `public.uei_crosswalk_2021.otherdrums.UPDATE`
- `public.uei_crosswalk_2021.web_anon.SELECT`
- `public.vw_appropriation_account_balances_download.otherdrums.DELETE`
- `public.vw_appropriation_account_balances_download.otherdrums.INSERT`
- `public.vw_appropriation_account_balances_download.otherdrums.REFERENCES`
- `public.vw_appropriation_account_balances_download.otherdrums.SELECT`
- `public.vw_appropriation_account_balances_download.otherdrums.TRIGGER`
- `public.vw_appropriation_account_balances_download.otherdrums.TRUNCATE`
- `public.vw_appropriation_account_balances_download.otherdrums.UPDATE`
- `public.vw_appropriation_account_balances_download.web_anon.SELECT`
- `public.vw_financial_accounts_by_awards_download.otherdrums.DELETE`
- `public.vw_financial_accounts_by_awards_download.otherdrums.INSERT`
- `public.vw_financial_accounts_by_awards_download.otherdrums.REFERENCES`
- `public.vw_financial_accounts_by_awards_download.otherdrums.SELECT`
- `public.vw_financial_accounts_by_awards_download.otherdrums.TRIGGER`
- `public.vw_financial_accounts_by_awards_download.otherdrums.TRUNCATE`
- `public.vw_financial_accounts_by_awards_download.otherdrums.UPDATE`
- `public.vw_financial_accounts_by_awards_download.web_anon.SELECT`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.DELETE`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.INSERT`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.REFERENCES`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.SELECT`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.TRIGGER`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.TRUNCATE`
- `public.vw_financial_accounts_by_program_activity_object_class_download.otherdrums.UPDATE`
- `public.vw_financial_accounts_by_program_activity_object_class_download.web_anon.SELECT`
- `public.vw_published_dabs_toptier_agency.otherdrums.DELETE`
- `public.vw_published_dabs_toptier_agency.otherdrums.INSERT`
- `public.vw_published_dabs_toptier_agency.otherdrums.REFERENCES`
- `public.vw_published_dabs_toptier_agency.otherdrums.SELECT`
- `public.vw_published_dabs_toptier_agency.otherdrums.TRIGGER`
- `public.vw_published_dabs_toptier_agency.otherdrums.TRUNCATE`
- `public.vw_published_dabs_toptier_agency.otherdrums.UPDATE`
- `public.vw_published_dabs_toptier_agency.web_anon.SELECT`
- `public.zips_grouped.otherdrums.DELETE`
- `public.zips_grouped.otherdrums.INSERT`
- `public.zips_grouped.otherdrums.REFERENCES`
- `public.zips_grouped.otherdrums.SELECT`
- `public.zips_grouped.otherdrums.TRIGGER`
- `public.zips_grouped.otherdrums.TRUNCATE`
- `public.zips_grouped.otherdrums.UPDATE`
- `public.zips_grouped.web_anon.SELECT`

**Only in `usaspending_bdp_validate`** (520)

- `public._staging_award_agg.postgres.DELETE`
- `public._staging_award_agg.postgres.INSERT`
- `public._staging_award_agg.postgres.REFERENCES`
- `public._staging_award_agg.postgres.SELECT`
- `public._staging_award_agg.postgres.TRIGGER`
- `public._staging_award_agg.postgres.TRUNCATE`
- `public._staging_award_agg.postgres.UPDATE`
- `public._staging_subaward_agg.postgres.DELETE`
- `public._staging_subaward_agg.postgres.INSERT`
- `public._staging_subaward_agg.postgres.REFERENCES`
- `public._staging_subaward_agg.postgres.SELECT`
- `public._staging_subaward_agg.postgres.TRIGGER`
- `public._staging_subaward_agg.postgres.TRUNCATE`
- `public._staging_subaward_agg.postgres.UPDATE`
- `public._staging_subaward_entities.postgres.DELETE`
- `public._staging_subaward_entities.postgres.INSERT`
- `public._staging_subaward_entities.postgres.REFERENCES`
- `public._staging_subaward_entities.postgres.SELECT`
- `public._staging_subaward_entities.postgres.TRIGGER`
- `public._staging_subaward_entities.postgres.TRUNCATE`
- `public._staging_subaward_entities.postgres.UPDATE`
- `public.agency.etl_user.DELETE`
- `public.agency.etl_user.INSERT`
- `public.agency.etl_user.REFERENCES`
- `public.agency.etl_user.SELECT`
- `public.agency.etl_user.TRIGGER`
- `public.agency.etl_user.TRUNCATE`
- `public.agency.etl_user.UPDATE`
- `public.ai_model.etl_user.DELETE`
- `public.ai_model.etl_user.INSERT`
- `public.ai_model.etl_user.REFERENCES`
- `public.ai_model.etl_user.SELECT`
- `public.ai_model.etl_user.TRIGGER`
- `public.ai_model.etl_user.TRUNCATE`
- `public.ai_model.etl_user.UPDATE`
- `public.appropriation_account_balances.etl_user.DELETE`
- `public.appropriation_account_balances.etl_user.INSERT`
- `public.appropriation_account_balances.etl_user.REFERENCES`
- `public.appropriation_account_balances.etl_user.SELECT`
- `public.appropriation_account_balances.etl_user.TRIGGER`
- `public.appropriation_account_balances.etl_user.TRUNCATE`
- `public.appropriation_account_balances.etl_user.UPDATE`
- `public.auth_group.etl_user.DELETE`
- `public.auth_group.etl_user.INSERT`
- `public.auth_group.etl_user.REFERENCES`
- `public.auth_group.etl_user.SELECT`
- `public.auth_group.etl_user.TRIGGER`
- `public.auth_group.etl_user.TRUNCATE`
- `public.auth_group.etl_user.UPDATE`
- `public.auth_group_permissions.etl_user.DELETE`
- `public.auth_group_permissions.etl_user.INSERT`
- `public.auth_group_permissions.etl_user.REFERENCES`
- `public.auth_group_permissions.etl_user.SELECT`
- `public.auth_group_permissions.etl_user.TRIGGER`
- `public.auth_group_permissions.etl_user.TRUNCATE`
- `public.auth_group_permissions.etl_user.UPDATE`
- `public.auth_permission.etl_user.DELETE`
- `public.auth_permission.etl_user.INSERT`
- `public.auth_permission.etl_user.REFERENCES`
- `public.auth_permission.etl_user.SELECT`
- `public.auth_permission.etl_user.TRIGGER`
- `public.auth_permission.etl_user.TRUNCATE`
- `public.auth_permission.etl_user.UPDATE`
- `public.auth_user.etl_user.DELETE`
- `public.auth_user.etl_user.INSERT`
- `public.auth_user.etl_user.REFERENCES`
- `public.auth_user.etl_user.SELECT`
- `public.auth_user.etl_user.TRIGGER`
- `public.auth_user.etl_user.TRUNCATE`
- `public.auth_user.etl_user.UPDATE`
- `public.auth_user_groups.etl_user.DELETE`
- `public.auth_user_groups.etl_user.INSERT`
- `public.auth_user_groups.etl_user.REFERENCES`
- `public.auth_user_groups.etl_user.SELECT`
- `public.auth_user_groups.etl_user.TRIGGER`
- `public.auth_user_groups.etl_user.TRUNCATE`
- `public.auth_user_groups.etl_user.UPDATE`
- `public.auth_user_user_permissions.etl_user.DELETE`
- `public.auth_user_user_permissions.etl_user.INSERT`
- `public.auth_user_user_permissions.etl_user.REFERENCES`
- `public.auth_user_user_permissions.etl_user.SELECT`
- `public.auth_user_user_permissions.etl_user.TRIGGER`
- `public.auth_user_user_permissions.etl_user.TRUNCATE`
- `public.auth_user_user_permissions.etl_user.UPDATE`
- `public.award_category.etl_user.DELETE`
- `public.award_category.etl_user.INSERT`
- `public.award_category.etl_user.REFERENCES`
- `public.award_category.etl_user.SELECT`
- `public.award_category.etl_user.TRIGGER`
- `public.award_category.etl_user.TRUNCATE`
- `public.award_category.etl_user.UPDATE`
- `public.budget_authority.etl_user.DELETE`
- `public.budget_authority.etl_user.INSERT`
- `public.budget_authority.etl_user.REFERENCES`
- `public.budget_authority.etl_user.SELECT`
- `public.budget_authority.etl_user.TRIGGER`
- `public.budget_authority.etl_user.TRUNCATE`
- `public.budget_authority.etl_user.UPDATE`
- `public.bureau_title_lookup.etl_user.DELETE`
- `public.bureau_title_lookup.etl_user.INSERT`
- `public.bureau_title_lookup.etl_user.REFERENCES`
- `public.bureau_title_lookup.etl_user.SELECT`
- `public.bureau_title_lookup.etl_user.TRIGGER`
- `public.bureau_title_lookup.etl_user.TRUNCATE`
- `public.bureau_title_lookup.etl_user.UPDATE`
- `public.c_to_d_linkage_updates.etl_user.DELETE`
- `public.c_to_d_linkage_updates.etl_user.INSERT`
- `public.c_to_d_linkage_updates.etl_user.REFERENCES`
- `public.c_to_d_linkage_updates.etl_user.SELECT`
- `public.c_to_d_linkage_updates.etl_user.TRIGGER`
- `public.c_to_d_linkage_updates.etl_user.TRUNCATE`
- `public.c_to_d_linkage_updates.etl_user.UPDATE`
- `public.cgac.etl_user.DELETE`
- `public.cgac.etl_user.INSERT`
- `public.cgac.etl_user.REFERENCES`
- `public.cgac.etl_user.SELECT`
- `public.cgac.etl_user.TRIGGER`
- `public.cgac.etl_user.TRUNCATE`
- `public.cgac.etl_user.UPDATE`
- `public.dabs_loader_queue.etl_user.DELETE`
- `public.dabs_loader_queue.etl_user.INSERT`
- `public.dabs_loader_queue.etl_user.REFERENCES`
- `public.dabs_loader_queue.etl_user.SELECT`
- `public.dabs_loader_queue.etl_user.TRIGGER`
- `public.dabs_loader_queue.etl_user.TRUNCATE`
- `public.dabs_loader_queue.etl_user.UPDATE`
- `public.dabs_submission_window_schedule.etl_user.DELETE`
- `public.dabs_submission_window_schedule.etl_user.INSERT`
- `public.dabs_submission_window_schedule.etl_user.REFERENCES`
- `public.dabs_submission_window_schedule.etl_user.SELECT`
- `public.dabs_submission_window_schedule.etl_user.TRIGGER`
- `public.dabs_submission_window_schedule.etl_user.TRUNCATE`
- `public.dabs_submission_window_schedule.etl_user.UPDATE`
- `public.disaster_emergency_fund_code.etl_user.DELETE`
- `public.disaster_emergency_fund_code.etl_user.INSERT`
- `public.disaster_emergency_fund_code.etl_user.REFERENCES`
- `public.disaster_emergency_fund_code.etl_user.SELECT`
- `public.disaster_emergency_fund_code.etl_user.TRIGGER`
- `public.disaster_emergency_fund_code.etl_user.TRUNCATE`
- `public.disaster_emergency_fund_code.etl_user.UPDATE`
- `public.django_admin_log.etl_user.DELETE`
- `public.django_admin_log.etl_user.INSERT`
- `public.django_admin_log.etl_user.REFERENCES`
- `public.django_admin_log.etl_user.SELECT`
- `public.django_admin_log.etl_user.TRIGGER`
- `public.django_admin_log.etl_user.TRUNCATE`
- `public.django_admin_log.etl_user.UPDATE`
- `public.django_content_type.etl_user.DELETE`
- `public.django_content_type.etl_user.INSERT`
- `public.django_content_type.etl_user.REFERENCES`
- `public.django_content_type.etl_user.SELECT`
- `public.django_content_type.etl_user.TRIGGER`
- `public.django_content_type.etl_user.TRUNCATE`
- `public.django_content_type.etl_user.UPDATE`
- `public.django_migrations.etl_user.DELETE`
- `public.django_migrations.etl_user.INSERT`
- `public.django_migrations.etl_user.REFERENCES`
- `public.django_migrations.etl_user.SELECT`
- `public.django_migrations.etl_user.TRIGGER`
- `public.django_migrations.etl_user.TRUNCATE`
- `public.django_migrations.etl_user.UPDATE`
- `public.django_session.etl_user.DELETE`
- `public.django_session.etl_user.INSERT`
- `public.django_session.etl_user.REFERENCES`
- `public.django_session.etl_user.SELECT`
- `public.django_session.etl_user.TRIGGER`
- `public.django_session.etl_user.TRUNCATE`
- `public.django_session.etl_user.UPDATE`
- `public.download_job.etl_user.DELETE`
- `public.download_job.etl_user.INSERT`
- `public.download_job.etl_user.REFERENCES`
- `public.download_job.etl_user.SELECT`
- `public.download_job.etl_user.TRIGGER`
- `public.download_job.etl_user.TRUNCATE`
- `public.download_job.etl_user.UPDATE`
- `public.download_job_lookup.etl_user.DELETE`
- `public.download_job_lookup.etl_user.INSERT`
- `public.download_job_lookup.etl_user.REFERENCES`
- `public.download_job_lookup.etl_user.SELECT`
- `public.download_job_lookup.etl_user.TRIGGER`
- `public.download_job_lookup.etl_user.TRUNCATE`
- `public.download_job_lookup.etl_user.UPDATE`
- `public.external_data_load_date.etl_user.DELETE`
- `public.external_data_load_date.etl_user.INSERT`
- `public.external_data_load_date.etl_user.REFERENCES`
- `public.external_data_load_date.etl_user.SELECT`
- `public.external_data_load_date.etl_user.TRIGGER`
- `public.external_data_load_date.etl_user.TRUNCATE`
- `public.external_data_load_date.etl_user.UPDATE`
- `public.external_data_type.etl_user.DELETE`
- `public.external_data_type.etl_user.INSERT`
- `public.external_data_type.etl_user.REFERENCES`
- `public.external_data_type.etl_user.SELECT`
- `public.external_data_type.etl_user.TRIGGER`
- `public.external_data_type.etl_user.TRUNCATE`
- `public.external_data_type.etl_user.UPDATE`
- `public.federal_account.etl_user.DELETE`
- `public.federal_account.etl_user.INSERT`
- `public.federal_account.etl_user.REFERENCES`
- `public.federal_account.etl_user.SELECT`
- `public.federal_account.etl_user.TRIGGER`
- `public.federal_account.etl_user.TRUNCATE`
- `public.federal_account.etl_user.UPDATE`
- `public.filter_hash.etl_user.DELETE`
- `public.filter_hash.etl_user.INSERT`
- `public.filter_hash.etl_user.REFERENCES`
- `public.filter_hash.etl_user.SELECT`
- `public.filter_hash.etl_user.TRIGGER`
- `public.filter_hash.etl_user.TRUNCATE`
- `public.filter_hash.etl_user.UPDATE`
- `public.financial_accounts_by_awards.etl_user.DELETE`
- `public.financial_accounts_by_awards.etl_user.INSERT`
- `public.financial_accounts_by_awards.etl_user.REFERENCES`
- `public.financial_accounts_by_awards.etl_user.SELECT`
- `public.financial_accounts_by_awards.etl_user.TRIGGER`
- `public.financial_accounts_by_awards.etl_user.TRUNCATE`
- `public.financial_accounts_by_awards.etl_user.UPDATE`
- `public.financial_accounts_by_program_activity_object_class.etl_user.DELETE`
- `public.financial_accounts_by_program_activity_object_class.etl_user.INSERT`
- `public.financial_accounts_by_program_activity_object_class.etl_user.REFERENCES`
- `public.financial_accounts_by_program_activity_object_class.etl_user.SELECT`
- `public.financial_accounts_by_program_activity_object_class.etl_user.TRIGGER`
- `public.financial_accounts_by_program_activity_object_class.etl_user.TRUNCATE`
- `public.financial_accounts_by_program_activity_object_class.etl_user.UPDATE`
- `public.frec.etl_user.DELETE`
- `public.frec.etl_user.INSERT`
- `public.frec.etl_user.REFERENCES`
- `public.frec.etl_user.SELECT`
- `public.frec.etl_user.TRIGGER`
- `public.frec.etl_user.TRUNCATE`
- `public.frec.etl_user.UPDATE`
- `public.frec_map.etl_user.DELETE`
- `public.frec_map.etl_user.INSERT`
- `public.frec_map.etl_user.REFERENCES`
- `public.frec_map.etl_user.SELECT`
- `public.frec_map.etl_user.TRIGGER`
- `public.frec_map.etl_user.TRUNCATE`
- `public.frec_map.etl_user.UPDATE`
- `public.gtas_sf133_balances.etl_user.DELETE`
- `public.gtas_sf133_balances.etl_user.INSERT`
- `public.gtas_sf133_balances.etl_user.REFERENCES`
- `public.gtas_sf133_balances.etl_user.SELECT`
- `public.gtas_sf133_balances.etl_user.TRIGGER`
- `public.gtas_sf133_balances.etl_user.TRUNCATE`
- `public.gtas_sf133_balances.etl_user.UPDATE`
- `public.historic_parent_duns.etl_user.DELETE`
- `public.historic_parent_duns.etl_user.INSERT`
- `public.historic_parent_duns.etl_user.REFERENCES`
- `public.historic_parent_duns.etl_user.SELECT`
- `public.historic_parent_duns.etl_user.TRIGGER`
- `public.historic_parent_duns.etl_user.TRUNCATE`
- `public.historic_parent_duns.etl_user.UPDATE`
- `public.historical_appropriation_account_balances.etl_user.DELETE`
- `public.historical_appropriation_account_balances.etl_user.INSERT`
- `public.historical_appropriation_account_balances.etl_user.REFERENCES`
- `public.historical_appropriation_account_balances.etl_user.SELECT`
- `public.historical_appropriation_account_balances.etl_user.TRIGGER`
- `public.historical_appropriation_account_balances.etl_user.TRUNCATE`
- `public.historical_appropriation_account_balances.etl_user.UPDATE`
- `public.job_status.etl_user.DELETE`
- `public.job_status.etl_user.INSERT`
- `public.job_status.etl_user.REFERENCES`
- `public.job_status.etl_user.SELECT`
- `public.job_status.etl_user.TRIGGER`
- `public.job_status.etl_user.TRUNCATE`
- `public.job_status.etl_user.UPDATE`
- `public.message.etl_user.DELETE`
- `public.message.etl_user.INSERT`
- `public.message.etl_user.REFERENCES`
- `public.message.etl_user.SELECT`
- `public.message.etl_user.TRIGGER`
- `public.message.etl_user.TRUNCATE`
- `public.message.etl_user.UPDATE`
- `public.naics.etl_user.DELETE`
- `public.naics.etl_user.INSERT`
- `public.naics.etl_user.REFERENCES`
- `public.naics.etl_user.SELECT`
- `public.naics.etl_user.TRIGGER`
- `public.naics.etl_user.TRUNCATE`
- `public.naics.etl_user.UPDATE`
- `public.object_class.etl_user.DELETE`
- `public.object_class.etl_user.INSERT`
- `public.object_class.etl_user.REFERENCES`
- `public.object_class.etl_user.SELECT`
- `public.object_class.etl_user.TRIGGER`
- `public.object_class.etl_user.TRUNCATE`
- `public.object_class.etl_user.UPDATE`
- `public.office.etl_user.DELETE`
- `public.office.etl_user.INSERT`
- `public.office.etl_user.REFERENCES`
- `public.office.etl_user.SELECT`
- `public.office.etl_user.TRIGGER`
- `public.office.etl_user.TRUNCATE`
- `public.office.etl_user.UPDATE`
- `public.overall_totals.etl_user.DELETE`
- `public.overall_totals.etl_user.INSERT`
- `public.overall_totals.etl_user.REFERENCES`
- `public.overall_totals.etl_user.SELECT`
- `public.overall_totals.etl_user.TRIGGER`
- `public.overall_totals.etl_user.TRUNCATE`
- `public.overall_totals.etl_user.UPDATE`
- `public.pg_stat_statements.postgres.DELETE`
- `public.pg_stat_statements.postgres.INSERT`
- `public.pg_stat_statements.postgres.REFERENCES`
- `public.pg_stat_statements.postgres.SELECT`
- `public.pg_stat_statements.postgres.TRIGGER`
- `public.pg_stat_statements.postgres.TRUNCATE`
- `public.pg_stat_statements.postgres.UPDATE`
- `public.pg_stat_statements_info.postgres.DELETE`
- `public.pg_stat_statements_info.postgres.INSERT`
- `public.pg_stat_statements_info.postgres.REFERENCES`
- `public.pg_stat_statements_info.postgres.SELECT`
- `public.pg_stat_statements_info.postgres.TRIGGER`
- `public.pg_stat_statements_info.postgres.TRUNCATE`
- `public.pg_stat_statements_info.postgres.UPDATE`
- `public.program_activity_park.etl_user.DELETE`
- `public.program_activity_park.etl_user.INSERT`
- `public.program_activity_park.etl_user.REFERENCES`
- `public.program_activity_park.etl_user.SELECT`
- `public.program_activity_park.etl_user.TRIGGER`
- `public.program_activity_park.etl_user.TRUNCATE`
- `public.program_activity_park.etl_user.UPDATE`
- `public.prompts.etl_user.DELETE`
- `public.prompts.etl_user.INSERT`
- `public.prompts.etl_user.REFERENCES`
- `public.prompts.etl_user.SELECT`
- `public.prompts.etl_user.TRIGGER`
- `public.prompts.etl_user.TRUNCATE`
- `public.prompts.etl_user.UPDATE`
- `public.psc.etl_user.DELETE`
- `public.psc.etl_user.INSERT`
- `public.psc.etl_user.REFERENCES`
- `public.psc.etl_user.SELECT`
- `public.psc.etl_user.TRIGGER`
- `public.psc.etl_user.TRUNCATE`
- `public.psc.etl_user.UPDATE`
- `public.recipient_geocode_index.api_user.SELECT`
- `public.ref_city_county_state_code.etl_user.DELETE`
- `public.ref_city_county_state_code.etl_user.INSERT`
- `public.ref_city_county_state_code.etl_user.REFERENCES`
- `public.ref_city_county_state_code.etl_user.SELECT`
- `public.ref_city_county_state_code.etl_user.TRIGGER`
- `public.ref_city_county_state_code.etl_user.TRUNCATE`
- `public.ref_city_county_state_code.etl_user.UPDATE`
- `public.ref_country_code.etl_user.DELETE`
- `public.ref_country_code.etl_user.INSERT`
- `public.ref_country_code.etl_user.REFERENCES`
- `public.ref_country_code.etl_user.SELECT`
- `public.ref_country_code.etl_user.TRIGGER`
- `public.ref_country_code.etl_user.TRUNCATE`
- `public.ref_country_code.etl_user.UPDATE`
- `public.ref_population_cong_district.etl_user.DELETE`
- `public.ref_population_cong_district.etl_user.INSERT`
- `public.ref_population_cong_district.etl_user.REFERENCES`
- `public.ref_population_cong_district.etl_user.SELECT`
- `public.ref_population_cong_district.etl_user.TRIGGER`
- `public.ref_population_cong_district.etl_user.TRUNCATE`
- `public.ref_population_cong_district.etl_user.UPDATE`
- `public.ref_population_county.etl_user.DELETE`
- `public.ref_population_county.etl_user.INSERT`
- `public.ref_population_county.etl_user.REFERENCES`
- `public.ref_population_county.etl_user.SELECT`
- `public.ref_population_county.etl_user.TRIGGER`
- `public.ref_population_county.etl_user.TRUNCATE`
- `public.ref_population_county.etl_user.UPDATE`
- `public.ref_program_activity.etl_user.DELETE`
- `public.ref_program_activity.etl_user.INSERT`
- `public.ref_program_activity.etl_user.REFERENCES`
- `public.ref_program_activity.etl_user.SELECT`
- `public.ref_program_activity.etl_user.TRIGGER`
- `public.ref_program_activity.etl_user.TRUNCATE`
- `public.ref_program_activity.etl_user.UPDATE`
- `public.references_cfda.etl_user.DELETE`
- `public.references_cfda.etl_user.INSERT`
- `public.references_cfda.etl_user.REFERENCES`
- `public.references_cfda.etl_user.SELECT`
- `public.references_cfda.etl_user.TRIGGER`
- `public.references_cfda.etl_user.TRUNCATE`
- `public.references_cfda.etl_user.UPDATE`
- `public.references_definition.etl_user.DELETE`
- `public.references_definition.etl_user.INSERT`
- `public.references_definition.etl_user.REFERENCES`
- `public.references_definition.etl_user.SELECT`
- `public.references_definition.etl_user.TRIGGER`
- `public.references_definition.etl_user.TRUNCATE`
- `public.references_definition.etl_user.UPDATE`
- `public.reporting_agency_missing_tas.etl_user.DELETE`
- `public.reporting_agency_missing_tas.etl_user.INSERT`
- `public.reporting_agency_missing_tas.etl_user.REFERENCES`
- `public.reporting_agency_missing_tas.etl_user.SELECT`
- `public.reporting_agency_missing_tas.etl_user.TRIGGER`
- `public.reporting_agency_missing_tas.etl_user.TRUNCATE`
- `public.reporting_agency_missing_tas.etl_user.UPDATE`
- `public.reporting_agency_overview.etl_user.DELETE`
- `public.reporting_agency_overview.etl_user.INSERT`
- `public.reporting_agency_overview.etl_user.REFERENCES`
- `public.reporting_agency_overview.etl_user.SELECT`
- `public.reporting_agency_overview.etl_user.TRIGGER`
- `public.reporting_agency_overview.etl_user.TRUNCATE`
- `public.reporting_agency_overview.etl_user.UPDATE`
- `public.reporting_agency_tas.etl_user.DELETE`
- `public.reporting_agency_tas.etl_user.INSERT`
- `public.reporting_agency_tas.etl_user.REFERENCES`
- `public.reporting_agency_tas.etl_user.SELECT`
- `public.reporting_agency_tas.etl_user.TRIGGER`
- `public.reporting_agency_tas.etl_user.TRUNCATE`
- `public.reporting_agency_tas.etl_user.UPDATE`
- `public.rest_framework_tracking_apirequestlog.etl_user.DELETE`
- `public.rest_framework_tracking_apirequestlog.etl_user.INSERT`
- `public.rest_framework_tracking_apirequestlog.etl_user.REFERENCES`
- `public.rest_framework_tracking_apirequestlog.etl_user.SELECT`
- `public.rest_framework_tracking_apirequestlog.etl_user.TRIGGER`
- `public.rest_framework_tracking_apirequestlog.etl_user.TRUNCATE`
- `public.rest_framework_tracking_apirequestlog.etl_user.UPDATE`
- `public.rosetta.etl_user.DELETE`
- `public.rosetta.etl_user.INSERT`
- `public.rosetta.etl_user.REFERENCES`
- `public.rosetta.etl_user.SELECT`
- `public.rosetta.etl_user.TRIGGER`
- `public.rosetta.etl_user.TRUNCATE`
- `public.rosetta.etl_user.UPDATE`
- `public.session.etl_user.DELETE`
- `public.session.etl_user.INSERT`
- `public.session.etl_user.REFERENCES`
- `public.session.etl_user.SELECT`
- `public.session.etl_user.TRIGGER`
- `public.session.etl_user.TRUNCATE`
- `public.session.etl_user.UPDATE`
- `public.state_data.etl_user.DELETE`
- `public.state_data.etl_user.INSERT`
- `public.state_data.etl_user.REFERENCES`
- `public.state_data.etl_user.SELECT`
- `public.state_data.etl_user.TRIGGER`
- `public.state_data.etl_user.TRUNCATE`
- `public.state_data.etl_user.UPDATE`
- `public.submission_attributes.etl_user.DELETE`
- `public.submission_attributes.etl_user.INSERT`
- `public.submission_attributes.etl_user.REFERENCES`
- `public.submission_attributes.etl_user.SELECT`
- `public.submission_attributes.etl_user.TRIGGER`
- `public.submission_attributes.etl_user.TRUNCATE`
- `public.submission_attributes.etl_user.UPDATE`
- `public.subtier_agency.etl_user.DELETE`
- `public.subtier_agency.etl_user.INSERT`
- `public.subtier_agency.etl_user.REFERENCES`
- `public.subtier_agency.etl_user.SELECT`
- `public.subtier_agency.etl_user.TRIGGER`
- `public.subtier_agency.etl_user.TRUNCATE`
- `public.subtier_agency.etl_user.UPDATE`
- `public.tool_use.etl_user.DELETE`
- `public.tool_use.etl_user.INSERT`
- `public.tool_use.etl_user.REFERENCES`
- `public.tool_use.etl_user.SELECT`
- `public.tool_use.etl_user.TRIGGER`
- `public.tool_use.etl_user.TRUNCATE`
- `public.tool_use.etl_user.UPDATE`
- `public.toptier_agency.etl_user.DELETE`
- `public.toptier_agency.etl_user.INSERT`
- `public.toptier_agency.etl_user.REFERENCES`
- `public.toptier_agency.etl_user.SELECT`
- `public.toptier_agency.etl_user.TRIGGER`
- `public.toptier_agency.etl_user.TRUNCATE`
- `public.toptier_agency.etl_user.UPDATE`
- `public.treasury_appropriation_account.etl_user.DELETE`
- `public.treasury_appropriation_account.etl_user.INSERT`
- `public.treasury_appropriation_account.etl_user.REFERENCES`
- `public.treasury_appropriation_account.etl_user.SELECT`
- `public.treasury_appropriation_account.etl_user.TRIGGER`
- `public.treasury_appropriation_account.etl_user.TRUNCATE`
- `public.treasury_appropriation_account.etl_user.UPDATE`
- `public.uei_crosswalk.api_user.SELECT`
- `public.uei_crosswalk.etl_user.DELETE`
- `public.uei_crosswalk.etl_user.INSERT`
- `public.uei_crosswalk.etl_user.REFERENCES`
- `public.uei_crosswalk.etl_user.SELECT`
- `public.uei_crosswalk.etl_user.TRIGGER`
- `public.uei_crosswalk.etl_user.TRUNCATE`
- `public.uei_crosswalk.etl_user.UPDATE`
- `public.uei_crosswalk_2021.etl_user.DELETE`
- `public.uei_crosswalk_2021.etl_user.INSERT`
- `public.uei_crosswalk_2021.etl_user.REFERENCES`
- `public.uei_crosswalk_2021.etl_user.SELECT`
- `public.uei_crosswalk_2021.etl_user.TRIGGER`
- `public.uei_crosswalk_2021.etl_user.TRUNCATE`
- `public.uei_crosswalk_2021.etl_user.UPDATE`
- `public.vw_appropriation_account_balances_download.etl_user.DELETE`
- `public.vw_appropriation_account_balances_download.etl_user.INSERT`
- `public.vw_appropriation_account_balances_download.etl_user.REFERENCES`
- `public.vw_appropriation_account_balances_download.etl_user.SELECT`
- `public.vw_appropriation_account_balances_download.etl_user.TRIGGER`
- `public.vw_appropriation_account_balances_download.etl_user.TRUNCATE`
- `public.vw_appropriation_account_balances_download.etl_user.UPDATE`
- `public.vw_financial_accounts_by_awards_download.etl_user.DELETE`
- `public.vw_financial_accounts_by_awards_download.etl_user.INSERT`
- `public.vw_financial_accounts_by_awards_download.etl_user.REFERENCES`
- `public.vw_financial_accounts_by_awards_download.etl_user.SELECT`
- `public.vw_financial_accounts_by_awards_download.etl_user.TRIGGER`
- `public.vw_financial_accounts_by_awards_download.etl_user.TRUNCATE`
- `public.vw_financial_accounts_by_awards_download.etl_user.UPDATE`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.DELETE`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.INSERT`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.REFERENCES`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.SELECT`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.TRIGGER`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.TRUNCATE`
- `public.vw_financial_accounts_by_program_activity_object_class_download.etl_user.UPDATE`
- `public.vw_published_dabs_toptier_agency.etl_user.DELETE`
- `public.vw_published_dabs_toptier_agency.etl_user.INSERT`
- `public.vw_published_dabs_toptier_agency.etl_user.REFERENCES`
- `public.vw_published_dabs_toptier_agency.etl_user.SELECT`
- `public.vw_published_dabs_toptier_agency.etl_user.TRIGGER`
- `public.vw_published_dabs_toptier_agency.etl_user.TRUNCATE`
- `public.vw_published_dabs_toptier_agency.etl_user.UPDATE`
- `public.zips_grouped.etl_user.DELETE`
- `public.zips_grouped.etl_user.INSERT`
- `public.zips_grouped.etl_user.REFERENCES`
- `public.zips_grouped.etl_user.SELECT`
- `public.zips_grouped.etl_user.TRIGGER`
- `public.zips_grouped.etl_user.TRUNCATE`
- `public.zips_grouped.etl_user.UPDATE`

## Content comparison

Row counts are advisory, never a gate. The reference database was built against an older upstream vintage; the candidate pulls current data. Differences are expected and are recorded here as the honest delta rather than treated as regressions. Counts are `reltuples` estimates, reported as unknown where a relation has never been analysed.

| Relation | Reference | Candidate | Delta | Change |
|---|---:|---:|---:|---:|
| `public._staging_award_agg` | unknown | 100,234 |  |  |
| `public._staging_subaward_agg` | unknown | 547 |  |  |
| `public._staging_subaward_entities` | unknown | 3,931 |  |  |
| `public.agency` | unknown | 1,530 |  |  |
| `public.agency_by_subtier_and_optionally_toptier` | 0 | 0 | +0 |  |
| `public.agency_lookup` | 0 | 0 | +0 |  |
| `public.ai_model` | unknown | 0 |  |  |
| `public.all_entities` | unknown | 17,769,136 |  |  |
| `public.appropriation_account_balances` | unknown | 655,096 |  |  |
| `public.auth_group` | unknown | 0 |  |  |
| `public.auth_group_permissions` | unknown | 0 |  |  |
| `public.auth_permission` | unknown | 579 |  |  |
| `public.auth_user` | unknown | 0 |  |  |
| `public.auth_user_groups` | unknown | 0 |  |  |
| `public.auth_user_user_permissions` | unknown | 0 |  |  |
| `public.award_category` | unknown | 14 |  |  |
| `public.budget_authority` | 7,661 | 7,661 | +0 | +0.0% |
| `public.bureau_title_lookup` | unknown | 5,496 |  |  |
| `public.c_to_d_linkage_updates` | unknown | 0 |  |  |
| `public.cgac` | unknown | 192 |  |  |
| `public.dabs_loader_queue` | unknown | 0 |  |  |
| `public.dabs_submission_window_schedule` | 112 | 112 | +0 | +0.0% |
| `public.disaster_emergency_fund_code` | 48 | 52 | +4 | +8.3% |
| `public.django_admin_log` | unknown | 0 |  |  |
| `public.django_content_type` | unknown | 156 |  |  |
| `public.django_migrations` | unknown | 279 |  |  |
| `public.django_session` | unknown | 0 |  |  |
| `public.download_job` | unknown | 0 |  |  |
| `public.download_job_lookup` | 4,518,172 | 0 | -4,518,172 | -100.0% |
| `public.entity_awards` | unknown | 389,347 |  |  |
| `public.external_data_load_date` | unknown | 15 |  |  |
| `public.external_data_type` | unknown | 16 |  |  |
| `public.federal_account` | unknown | 3,437 |  |  |
| `public.filter_hash` | unknown | 0 |  |  |
| `public.financial_accounts_by_awards` | 446,236,576 | 32,629,768 | -413,606,808 | -92.7% |
| `public.financial_accounts_by_program_activity_object_class` | unknown | 10,649,845 |  |  |
| `public.frec` | unknown | 166 |  |  |
| `public.frec_map` | unknown | 13,464 |  |  |
| `public.gtas_sf133_balances` | unknown | 988,149 |  |  |
| `public.historic_parent_duns` | unknown | 3,198,161 |  |  |
| `public.historical_appropriation_account_balances` | unknown | 249,643 |  |  |
| `public.job_status` | unknown | 8 |  |  |
| `public.message` | unknown | 0 |  |  |
| `public.mv_agency_autocomplete` | 0 | 0 | +0 |  |
| `public.mv_agency_office_autocomplete` | 0 | 0 | +0 |  |
| `public.mv_covid_spending` | unknown | 0 |  |  |
| `public.mv_district_spending` | unknown | 0 |  |  |
| `public.mv_entity_spending_summary` | unknown | 0 |  |  |
| `public.naics` | unknown | 1,741 |  |  |
| `public.object_class` | unknown | 105 |  |  |
| `public.office` | unknown | 86,587 |  |  |
| `public.overall_totals` | unknown | 141 |  |  |
| `public.prime_awards` | unknown | 360,535 |  |  |
| `public.program_activity_park` | unknown | 9,141 |  |  |
| `public.prompts` | unknown | 0 |  |  |
| `public.psc` | unknown | 3,836 |  |  |
| `public.recipient_geocode_index` | unknown | 1,993 |  |  |
| `public.ref_city_county_state_code` | unknown | 202,520 |  |  |
| `public.ref_country_code` | unknown | 260 |  |  |
| `public.ref_population_cong_district` | unknown | 441 |  |  |
| `public.ref_population_county` | unknown | 3,290 |  |  |
| `public.ref_program_activity` | unknown | 79,173 |  |  |
| `public.references_cfda` | 3,816 | 4,178 | +362 | +9.5% |
| `public.references_definition` | unknown | 151 |  |  |
| `public.reporting_agency_missing_tas` | unknown | 305,175 |  |  |
| `public.reporting_agency_overview` | unknown | 11,322 |  |  |
| `public.reporting_agency_tas` | unknown | 653,891 |  |  |
| `public.rest_framework_tracking_apirequestlog` | unknown | 0 |  |  |
| `public.rosetta` | unknown | 1 |  |  |
| `public.session` | unknown | 0 |  |  |
| `public.state_data` | unknown | 448 |  |  |
| `public.subawards` | unknown | 28,669 |  |  |
| `public.submission_attributes` | unknown | 7,799 |  |  |
| `public.subtier_agency` | unknown | 1,490 |  |  |
| `public.tas_autocomplete_matview` | 0 | 0 | +0 |  |
| `public.tool_use` | unknown | 0 |  |  |
| `public.toptier_agency` | unknown | 198 |  |  |
| `public.treasury_appropriation_account` | unknown | 25,576 |  |  |
| `public.uei_crosswalk` | 3,323,130 | 3,323,130 | +0 | +0.0% |
| `public.uei_crosswalk_2021` | unknown | 3,279,911 |  |  |
| `public.zips_grouped` | unknown | 53,646 |  |  |

