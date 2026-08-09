-- RECOVERED INDEX DDL -- derived objects
-- provenance: recovered
--
-- Indexes on materialized views created by stage 06_derive. Extracted verbatim
-- from pg_indexes on 2026-08-08; no known ETL script creates them.
--
-- Applied at the end of 06_derive, after the views are materialized.


-- public.all_entities
CREATE INDEX IF NOT EXISTS idx_ae_duns ON public.all_entities USING btree (duns);
CREATE INDEX IF NOT EXISTS idx_ae_uei ON public.all_entities USING btree (uei);

-- public.entity_awards
CREATE INDEX IF NOT EXISTS idx_ea_award_id ON public.entity_awards USING btree (award_id);
CREATE INDEX IF NOT EXISTS idx_ea_entity_id ON public.entity_awards USING btree (entity_id);
CREATE INDEX IF NOT EXISTS idx_ea_entity_id_action_date ON public.entity_awards USING btree (entity_id, action_date DESC);

-- public.mv_covid_spending
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcs_fy ON public.mv_covid_spending USING btree (fiscal_year);

-- public.mv_district_spending
CREATE INDEX IF NOT EXISTS idx_mds_fiscal_year ON public.mv_district_spending USING btree (fiscal_year);
CREATE INDEX IF NOT EXISTS idx_mds_obligation ON public.mv_district_spending USING btree (total_obligation DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mds_state_dist_fy ON public.mv_district_spending USING btree (state, district, fiscal_year);

-- public.mv_entity_spending_summary
CREATE INDEX IF NOT EXISTS idx_mess_agency ON public.mv_entity_spending_summary USING btree (top_awarding_agency);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mess_entity_id ON public.mv_entity_spending_summary USING btree (entity_id);
CREATE INDEX IF NOT EXISTS idx_mess_geom ON public.mv_entity_spending_summary USING gist (geom_point) WHERE (geom_point IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_mess_name_trgm ON public.mv_entity_spending_summary USING gin (legal_business_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mess_obligation ON public.mv_entity_spending_summary USING btree (total_obligation DESC);
CREATE INDEX IF NOT EXISTS idx_mess_state ON public.mv_entity_spending_summary USING btree (state);
CREATE INDEX IF NOT EXISTS idx_mess_uei ON public.mv_entity_spending_summary USING btree (uei);

-- public.subawards
CREATE INDEX IF NOT EXISTS idx_subawards_sub_recipient_duns ON public.subawards USING btree (sub_recipient_duns) WHERE (sub_recipient_duns IS NOT NULL);
