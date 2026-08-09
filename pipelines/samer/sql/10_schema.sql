-- ============================================================================
-- samer: base tables and sequences (stage 03_schema)
--
-- PROVENANCE: extracted from the live `sam_er` catalog on 2026-08-08 with
--     pg_dump --schema-only --section=pre-data --no-owner --no-privileges \
--             --no-comments -n public sam_er
--
-- Made idempotent (IF NOT EXISTS) so the stage runs against an empty server
-- or an existing database. Derived objects (views, materialized views, RPC
-- functions) live in 30_derive.sql; constraints and indexes in
-- 20_constraints.sql. See MIGRATION.md for the provenance attribution table.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.sam_registrations (
    id integer NOT NULL,
    uei character varying(50) NOT NULL,
    entity_id character varying(50),
    duns character varying(20),
    legal_business_name character varying(255),
    dba_name character varying(255),
    physical_address_line1 text,
    physical_city character varying(100),
    physical_state character varying(100),
    physical_zip character varying(20),
    physical_country character varying(10),
    mailing_address_line1 text,
    mailing_city character varying(100),
    mailing_state character varying(100),
    mailing_zip character varying(50),
    mailing_country character varying(10),
    primary_naics character varying(10),
    naics_codes text,
    psc_codes text,
    registration_expiration character varying(20),
    last_update character varying(20),
    business_start_date character varying(20),
    corporate_url text,
    purpose_of_registration character varying(50),
    source_file character varying(255),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_current boolean DEFAULT true,
    latitude double precision,
    longitude double precision,
    geocode_date timestamp without time zone,
    geocode_system character varying(50),
    geom_point public.geometry(Point,4326)
);

CREATE SEQUENCE IF NOT EXISTS public.sam_registrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.sam_registrations_id_seq OWNED BY public.sam_registrations.id;

ALTER TABLE ONLY public.sam_registrations ALTER COLUMN id SET DEFAULT nextval('public.sam_registrations_id_seq'::regclass);
