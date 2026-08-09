-- RECOVERED DDL
-- provenance: recovered
--
-- This object exists in the live benthic.io database but has no source in any
-- known ETL script. It was created ad hoc via psql. The definition below was
-- extracted from the live catalog on 2026-08-08 and is reproduced verbatim so
-- that the object becomes auditable and reproducible.
--
-- database: usaspending_db
-- object:   mv_entity_spending_summary
-- kind:     materialized view

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_entity_spending_summary AS
 SELECT e.entity_id,
    e.legal_business_name,
    e.uei,
    e.duns,
    e.state,
    e.city,
    e.latitude,
    e.longitude,
    e.geom_point,
    e.award_count,
    e.total_obligation,
    e.date_first_award,
    e.date_last_award,
    e.prime_subaward_count,
    e.prime_subaward_amount,
    ea.awarding_agency AS top_awarding_agency,
    ea.award_type AS most_recent_award_type,
    ea.action_date AS most_recent_action_date
   FROM all_entities e
     LEFT JOIN ( SELECT DISTINCT ON (entity_awards.entity_id) entity_awards.entity_id,
            entity_awards.awarding_agency,
            entity_awards.award_type,
            entity_awards.action_date
           FROM entity_awards
          ORDER BY entity_awards.entity_id, entity_awards.action_date DESC) ea ON ea.entity_id = e.entity_id
  WHERE e.total_obligation IS NOT NULL
WITH NO DATA;
