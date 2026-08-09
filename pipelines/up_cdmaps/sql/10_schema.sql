-- ============================================================================
-- up_cdmaps: base tables and sequences (stage 03_schema)
--
-- PROVENANCE: extracted from the live `ucla_polysci_cdmaps` catalog on 2026-08-08 with
--     pg_dump --schema-only --section=pre-data --no-owner --no-privileges \
--             --no-comments -n public ucla_polysci_cdmaps
--
-- Made idempotent (IF NOT EXISTS) so the stage runs against an empty server
-- or an existing database. Derived objects (views, materialized views, RPC
-- functions) live in 30_derive.sql; constraints and indexes in
-- 20_constraints.sql. See MIGRATION.md for the provenance attribution table.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.congressional_districts (
    id integer NOT NULL,
    congress_number integer NOT NULL,
    statename character varying(80),
    district integer,
    startcong numeric(24,15),
    endcong numeric(24,15),
    district_id character varying(80),
    districtsi character varying(254),
    county character varying(227),
    page character varying(227),
    law character varying(254),
    note character varying(254),
    bestdec character varying(254),
    finalnote character varying(254),
    rnote character varying(254),
    lastchange date,
    fromcounty character varying(80),
    statefp character varying(80),
    geom public.geometry(MultiPolygon,3857),
    source_file character varying(255),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.congressional_districts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.congressional_districts_id_seq OWNED BY public.congressional_districts.id;

ALTER TABLE ONLY public.congressional_districts ALTER COLUMN id SET DEFAULT nextval('public.congressional_districts_id_seq'::regclass);
