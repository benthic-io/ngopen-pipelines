-- ============================================================================
-- usp_cl: base tables and sequences (stage 03_schema)
--
-- PROVENANCE: extracted from the live `us_project_cl` catalog on 2026-08-08 with
--     pg_dump --schema-only --section=pre-data --no-owner --no-privileges \
--             --no-comments -n public us_project_cl
--
-- Made idempotent (IF NOT EXISTS) so the stage runs against an empty server
-- or an existing database. Derived objects (views, materialized views, RPC
-- functions) live in 30_derive.sql; constraints and indexes in
-- 20_constraints.sql. See MIGRATION.md for the provenance attribution table.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.committee_membership (
    membership_id integer NOT NULL,
    committee_thomas_id character varying(20),
    bioguide_id character varying(10),
    legislator_name character varying(255),
    party character varying(20),
    rank integer,
    title character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.committee_membership_membership_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.committee_membership_membership_id_seq OWNED BY public.committee_membership.membership_id;

CREATE TABLE IF NOT EXISTS public.committees (
    committee_id integer NOT NULL,
    thomas_id character varying(20),
    house_committee_id character varying(10),
    senate_committee_id character varying(10),
    committee_type character varying(20),
    name character varying(255),
    url character varying(500),
    minority_url character varying(500),
    address text,
    phone character varying(50),
    jurisdiction text,
    rss_url character varying(500),
    youtube_id character varying(50),
    congresses integer[],
    is_current boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.committees_committee_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.committees_committee_id_seq OWNED BY public.committees.committee_id;

CREATE TABLE IF NOT EXISTS public.district_offices (
    office_id integer NOT NULL,
    bioguide_id character varying(10),
    office_key character varying(100),
    address text,
    suite character varying(255),
    building character varying(255),
    city character varying(100),
    state character(2),
    zip character varying(20),
    latitude double precision,
    longitude double precision,
    phone character varying(50),
    fax character varying(50),
    hours text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    geom_point public.geometry(Point,4326)
);

CREATE SEQUENCE IF NOT EXISTS public.district_offices_office_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.district_offices_office_id_seq OWNED BY public.district_offices.office_id;

CREATE TABLE IF NOT EXISTS public.executive_terms (
    term_id integer NOT NULL,
    bioguide_id character varying(10),
    term_type character varying(20),
    start_date date,
    end_date date,
    party character varying(50),
    how character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.executive_terms_term_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.executive_terms_term_id_seq OWNED BY public.executive_terms.term_id;

CREATE TABLE IF NOT EXISTS public.executives (
    bioguide_id character varying(10) NOT NULL,
    govtrack_id integer,
    icpsr_prez_id integer,
    first_name character varying(100),
    middle_name character varying(100),
    last_name character varying(100),
    suffix character varying(20),
    birthday date,
    gender character(1),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.legislator_other_names (
    name_id integer NOT NULL,
    bioguide_id character varying(10),
    first_name character varying(100),
    middle_name character varying(100),
    last_name character varying(100),
    suffix character varying(20),
    start_date date,
    end_date date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.legislator_other_names_name_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.legislator_other_names_name_id_seq OWNED BY public.legislator_other_names.name_id;

CREATE TABLE IF NOT EXISTS public.legislator_social_media (
    social_id integer NOT NULL,
    bioguide_id character varying(10),
    twitter character varying(100),
    twitter_id character varying(50),
    facebook character varying(100),
    facebook_id bigint,
    youtube character varying(100),
    youtube_id character varying(100),
    instagram character varying(100),
    instagram_id bigint,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.legislator_social_media_social_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.legislator_social_media_social_id_seq OWNED BY public.legislator_social_media.social_id;

CREATE TABLE IF NOT EXISTS public.legislator_terms (
    term_id integer NOT NULL,
    bioguide_id character varying(10),
    congress_start character varying(3),
    congress_end character varying(3),
    term_start date,
    term_end date,
    term_type character varying(10),
    state character(2),
    district integer,
    class integer,
    state_rank character varying(10),
    party character varying(50),
    url character varying(500),
    address text,
    phone character varying(50),
    fax character varying(50),
    contact_form character varying(500),
    office character varying(255),
    rss_url character varying(500),
    how character varying(50),
    end_type character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.legislator_terms_term_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.legislator_terms_term_id_seq OWNED BY public.legislator_terms.term_id;

CREATE TABLE IF NOT EXISTS public.legislators (
    bioguide_id character varying(10) NOT NULL,
    thomas_id character varying(10),
    lis_id character varying(10),
    govtrack_id integer,
    opensecrets_id character varying(20),
    votesmart_id integer,
    cspan_id integer,
    wikipedia_page character varying(255),
    ballotpedia_page character varying(255),
    maplight_id integer,
    house_history_id bigint,
    icpsr_id integer,
    wikidata_id character varying(20),
    google_entity_id character varying(100),
    pictorial_id integer,
    fec_ids text[],
    bioguide_previous text[],
    first_name character varying(100),
    middle_name character varying(100),
    last_name character varying(100),
    suffix character varying(20),
    nickname character varying(100),
    official_full character varying(255),
    birthday date,
    gender character(1),
    is_current boolean DEFAULT false,
    first_term_start date,
    last_term_end date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.subcommittees (
    subcommittee_id integer NOT NULL,
    committee_id integer,
    thomas_id character varying(10),
    name character varying(255),
    address text,
    phone character varying(50),
    congresses integer[],
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.subcommittees_subcommittee_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.subcommittees_subcommittee_id_seq OWNED BY public.subcommittees.subcommittee_id;

ALTER TABLE ONLY public.committee_membership ALTER COLUMN membership_id SET DEFAULT nextval('public.committee_membership_membership_id_seq'::regclass);

ALTER TABLE ONLY public.committees ALTER COLUMN committee_id SET DEFAULT nextval('public.committees_committee_id_seq'::regclass);

ALTER TABLE ONLY public.district_offices ALTER COLUMN office_id SET DEFAULT nextval('public.district_offices_office_id_seq'::regclass);

ALTER TABLE ONLY public.executive_terms ALTER COLUMN term_id SET DEFAULT nextval('public.executive_terms_term_id_seq'::regclass);

ALTER TABLE ONLY public.legislator_other_names ALTER COLUMN name_id SET DEFAULT nextval('public.legislator_other_names_name_id_seq'::regclass);

ALTER TABLE ONLY public.legislator_social_media ALTER COLUMN social_id SET DEFAULT nextval('public.legislator_social_media_social_id_seq'::regclass);

ALTER TABLE ONLY public.legislator_terms ALTER COLUMN term_id SET DEFAULT nextval('public.legislator_terms_term_id_seq'::regclass);

ALTER TABLE ONLY public.subcommittees ALTER COLUMN subcommittee_id SET DEFAULT nextval('public.subcommittees_subcommittee_id_seq'::regclass);
