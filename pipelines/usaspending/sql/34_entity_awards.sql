-- Extracted verbatim from ngopen/build_entity_awards.py (SQL_ENTITY_AWARDS)
-- Source commit: c4dd142  Extracted: 2026-08-08
DROP MATERIALIZED VIEW IF EXISTS public.entity_awards CASCADE;

CREATE MATERIALIZED VIEW public.entity_awards AS
SELECT * FROM (
    SELECT 
        ae.entity_id,
        ae.legal_business_name AS entity_name,
        ae.uei AS entity_uei,
        ae.duns AS entity_duns,
        ae.parent_uei AS entity_parent_uei,
        ae.state AS entity_state,
        ae.city AS entity_city,
        ae.geohash_6 AS entity_geohash,
        ae.geom_point AS entity_geom,
        ae.is_geocoded,
        'prime' AS award_type,
        pa.award_id,
        pa.fiscal_year,
        pa.action_date,
        pa.total_obligation,
        pa.award_amount,
        pa.awarding_agency,
        pa.recipient_name,
        pa.recipient_state,
        pa.recipient_city,
        pa.pop_state,
        pa.description,
        pa.piid,
        pa.fain,
        pa.category,
        pa.naics_code,
        pa.product_or_service_code,
        pa.recipient_uei,
        pa.link_method
    FROM public.all_entities ae
    JOIN public.prime_awards pa ON ae.entity_id = pa.linked_entity_id
    
    UNION ALL
    
    SELECT 
        ae.entity_id,
        ae.legal_business_name AS entity_name,
        ae.uei AS entity_uei,
        ae.duns AS entity_duns,
        ae.parent_uei AS entity_parent_uei,
        ae.state AS entity_state,
        ae.city AS entity_city,
        ae.geohash_6 AS entity_geohash,
        ae.geom_point AS entity_geom,
        ae.is_geocoded,
        'subaward' AS award_type,
        sa.subaward_id AS award_id,
        sa.fiscal_year,
        sa.sub_action_date AS action_date,
        sa.subaward_amount AS total_obligation,
        sa.prime_award_amount AS award_amount,
        sa.awarding_agency_name AS awarding_agency,
        sa.sub_recipient_name AS recipient_name,
        sa.sub_state AS recipient_state,
        sa.sub_city AS recipient_city,
        sa.pop_state,
        sa.subaward_description AS description,
        sa.prime_award_piid_fain AS piid,
        NULL AS fain,
        NULL AS category,
        sa.sub_naics AS naics_code,
        NULL AS product_or_service_code,
        sa.sub_recipient_uei AS recipient_uei,
        sa.sub_link_method AS link_method
    FROM public.all_entities ae
    JOIN public.subawards sa ON ae.entity_id = sa.linked_sub_entity_id
) combined;

CREATE UNIQUE INDEX idx_entity_awards_id ON public.entity_awards(award_id, award_type);
CREATE INDEX idx_entity_awards_entity_id ON public.entity_awards(entity_id);
CREATE INDEX idx_entity_awards_entity_fy ON public.entity_awards(entity_id, fiscal_year);
CREATE INDEX idx_entity_awards_geohash ON public.entity_awards(entity_geohash) WHERE entity_geohash IS NOT NULL;
CREATE INDEX idx_entity_awards_name ON public.entity_awards USING gin(entity_name gin_trgm_ops);
CREATE INDEX idx_entity_awards_fiscal_year ON public.entity_awards(fiscal_year);
CREATE INDEX idx_entity_awards_action_date ON public.entity_awards(action_date);
CREATE INDEX idx_entity_awards_award_type ON public.entity_awards(award_type);
CREATE INDEX idx_entity_awards_state ON public.entity_awards(entity_state) WHERE entity_state IS NOT NULL;

GRANT SELECT ON public.entity_awards TO postgres;
