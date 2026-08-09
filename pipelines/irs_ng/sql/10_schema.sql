-- ============================================================================
-- irs_ng: base tables and sequences (stage 03_schema)
--
-- PROVENANCE: extracted from the live `irs_ng` catalog on 2026-08-08 with
--     pg_dump --schema-only --section=pre-data --no-owner --no-privileges \
--             --no-comments -n public irs_ng
--
-- Made idempotent (IF NOT EXISTS) so the stage runs against an empty server
-- or an existing database. Derived objects (views, materialized views, RPC
-- functions) live in 30_derive.sql; constraints and indexes in
-- 20_constraints.sql. See MIGRATION.md for the provenance attribution table.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.bmf_organization_snapshots (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    release_date date NOT NULL,
    release_source character varying(255) NOT NULL,
    org_name character varying(500),
    bmf_status_code character varying(10),
    bmf_subsection_code character varying(10),
    ntee_irs character varying(10),
    f990_org_addr_city character varying(100),
    f990_org_addr_state character varying(10),
    f990_org_addr_street text,
    f990_org_addr_zip character varying(20),
    f990_total_revenue bigint,
    f990_total_income bigint,
    f990_total_assets bigint,
    org_ruling_date character varying(20),
    org_year_first character varying(10),
    org_year_last character varying(10)
);

CREATE SEQUENCE IF NOT EXISTS public.bmf_organization_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.bmf_organization_snapshots_id_seq OWNED BY public.bmf_organization_snapshots.id;

CREATE TABLE IF NOT EXISTS public.bmf_organizations (
    id integer NOT NULL,
    ein character varying(20),
    ein2 character varying(100),
    ntee_irs character varying(10),
    ntee_nccs character varying(10),
    nteev2 character varying(100),
    nccs_level_1 character varying(100),
    nccs_level_2 character varying(10),
    nccs_level_3 character varying(10),
    f990_total_revenue_recent bigint,
    f990_total_income_recent bigint,
    f990_total_assets_recent bigint,
    f990_org_addr_city character varying(100),
    f990_org_addr_state character varying(10),
    f990_org_addr_zip character varying(20),
    f990_org_addr_street text,
    census_cbsa_fips character varying(20),
    census_cbsa_name character varying(200),
    census_block_fips character varying(20),
    census_urban_area character varying(200),
    census_state_abbr character varying(10),
    census_county_name character varying(100),
    org_addr_full text,
    org_addr_match character varying(200),
    latitude numeric(10,8),
    longitude numeric(11,8),
    geocoder_score numeric(5,2),
    geocoder_match character varying(100),
    geocode_date timestamp with time zone,
    geocoding_source character varying(50),
    bmf_subsection_code character varying(10),
    bmf_status_code character varying(10),
    bmf_pf_filing_req_code character varying(10),
    bmf_organization_code character varying(10),
    bmf_income_code character varying(10),
    bmf_group_exempt_num character varying(50),
    bmf_foundation_code character varying(10),
    bmf_filing_req_code character varying(10),
    bmf_deductibility_code character varying(10),
    bmf_classification_code character varying(10),
    bmf_asset_code character varying(10),
    bmf_affiliation_code character varying(10),
    org_ruling_date character varying(20),
    org_fiscal_year character varying(10),
    org_ruling_year character varying(10),
    org_year_first character varying(10),
    org_year_last character varying(10),
    org_year_count integer,
    org_pers_ico character varying(100),
    org_name_sec text,
    org_name_current text,
    org_fiscal_period character varying(10),
    source_file character varying(255),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_current boolean DEFAULT true,
    geom_point public.geometry(Point,4326)
);

CREATE SEQUENCE IF NOT EXISTS public.bmf_organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.bmf_organizations_id_seq OWNED BY public.bmf_organizations.id;

CREATE TABLE IF NOT EXISTS public.census_demographics (
    id integer NOT NULL,
    geoid character varying(20),
    geo_type character varying(10),
    year integer,
    total_population integer,
    median_household_income integer,
    poverty_count integer,
    white_count integer,
    black_count integer,
    hispanic_count integer,
    bachelors_count integer,
    housing_units integer,
    median_housing_value integer,
    source_file character varying(255)
);

CREATE SEQUENCE IF NOT EXISTS public.census_demographics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.census_demographics_id_seq OWNED BY public.census_demographics.id;

CREATE TABLE IF NOT EXISTS public.form990_details (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    tax_period character varying(10),
    form_type character varying(10),
    filing_date date,
    total_revenue bigint,
    contributions_received bigint,
    program_service_revenue bigint,
    total_expenses bigint,
    grants_paid bigint,
    total_assets bigint,
    total_liabilities bigint,
    net_assets bigint,
    source_file character varying(255),
    xml_path character varying(500),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    has_disregarded_entity boolean DEFAULT false,
    has_related_entity boolean DEFAULT false,
    has_related_org_control boolean DEFAULT false,
    has_transfer_to_noncharitable boolean DEFAULT false,
    has_partnership_activity boolean DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS public.form990_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990_details_id_seq OWNED BY public.form990_details.id;

CREATE TABLE IF NOT EXISTS public.form990_schedule_o (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    tax_period character varying(6),
    form_type character varying(10),
    program_accomplishments text,
    governance_text text,
    supplemental_info text,
    source_file character varying(255),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.form990_schedule_o_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990_schedule_o_id_seq OWNED BY public.form990_schedule_o.id;

CREATE TABLE IF NOT EXISTS public.form990_soi (
    id integer NOT NULL,
    ein character varying(20),
    tax_year integer NOT NULL,
    org_name character varying(500),
    state character varying(10),
    ntee_code character varying(10),
    asset_size character varying(20),
    total_revenue bigint,
    total_expenses bigint,
    total_assets bigint,
    total_liabilities bigint,
    net_assets bigint,
    contributions bigint,
    grants_paid bigint,
    compensation_officers bigint,
    revenue_less_expenses bigint,
    total_programs bigint,
    source_file character varying(255),
    form_type character varying(10),
    subseccd character varying(5),
    is_501c3 boolean,
    total_program_revenue bigint,
    investment_income bigint,
    royalty_income bigint,
    net_rental_income bigint,
    net_gains_losses bigint,
    fundraising_income bigint,
    gaming_income bigint,
    tax_exempt_interest bigint,
    legal_fees bigint,
    accounting_fees bigint,
    professional_fundraising bigint,
    management_fees bigint,
    investment_mgmt_fees bigint,
    advertising bigint,
    office_expenses bigint,
    occupancy bigint,
    travel bigint,
    insurance bigint,
    depreciation bigint,
    interest_expense bigint,
    other_salaries_wages bigint,
    pension_contributions bigint,
    employee_benefits bigint,
    payroll_taxes bigint,
    total_reportable_comp bigint,
    total_estimated_comp bigint,
    individuals_over_100k integer,
    land_buildings_equipment bigint,
    investments_end bigint,
    cash_end bigint,
    num_employees integer,
    num_orgs integer,
    total_support bigint,
    non_pf_reason character varying(5),
    filed_990t boolean,
    unrelated_business_income boolean,
    foreign_offices boolean,
    political_activities boolean,
    lobbying_activities boolean,
    operates_hospital boolean,
    donor_advised_funds boolean
);

CREATE SEQUENCE IF NOT EXISTS public.form990_soi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990_soi_id_seq OWNED BY public.form990_soi.id;

CREATE TABLE IF NOT EXISTS public.form990_soi_private_foundation (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    tax_year integer NOT NULL,
    tax_period character varying(6),
    operating_cd character varying(5),
    fair_market_value bigint,
    gross_contributions bigint,
    interest_revenue bigint,
    dividends bigint,
    gross_rents bigint,
    gross_sales_price bigint,
    cost_of_goods_sold bigint,
    gross_profit_business bigint,
    other_income bigint,
    total_receipts_books bigint,
    compensation_officers bigint,
    pension_benefits bigint,
    legal_fees bigint,
    accounting_fees bigint,
    interest_expense bigint,
    depreciation bigint,
    occupancy bigint,
    travel_conferences bigint,
    printing_publications bigint,
    total_expenses_books bigint,
    contributions_paid bigint,
    excess_receipts bigint,
    net_investment_income bigint,
    adjusted_net_income bigint,
    total_cash bigint,
    investments_govt_obligations bigint,
    investments_corp_stock bigint,
    investments_corp_bonds bigint,
    total_investment_securities bigint,
    mortgage_loans bigint,
    other_investments bigint,
    other_assets bigint,
    total_assets bigint,
    mortgage_notes_payable bigint,
    other_liabilities bigint,
    total_liabilities bigint,
    fund_net_worth bigint,
    fair_market_value_eoy bigint,
    tax_due bigint,
    excise_tax bigint,
    distributions bigint,
    undistributed_income bigint,
    qualifying_distributions bigint,
    minimum_investment_return bigint,
    grants_approved_future bigint,
    is_operating boolean,
    source_file character varying(255)
);

CREATE SEQUENCE IF NOT EXISTS public.form990_soi_private_foundation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990_soi_private_foundation_id_seq OWNED BY public.form990_soi_private_foundation.id;

CREATE TABLE IF NOT EXISTS public.form990_xml_import_log (
    id integer NOT NULL,
    zip_filename character varying(255) NOT NULL,
    xml_count integer,
    records_imported integer DEFAULT 0,
    records_990 integer DEFAULT 0,
    records_990t integer DEFAULT 0,
    schedule_o_count integer DEFAULT 0,
    import_started_at timestamp without time zone,
    import_completed_at timestamp without time zone,
    import_status character varying(20),
    notes text
);

CREATE SEQUENCE IF NOT EXISTS public.form990_xml_import_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990_xml_import_log_id_seq OWNED BY public.form990_xml_import_log.id;

CREATE TABLE IF NOT EXISTS public.form990n_small_orgs (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    org_name character varying(500),
    tax_period character varying(20),
    website character varying(500),
    source_file character varying(255),
    downloaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.form990n_small_orgs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990n_small_orgs_id_seq OWNED BY public.form990n_small_orgs.id;

CREATE TABLE IF NOT EXISTS public.form990t_details (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    tax_period character varying(10),
    filing_date date,
    organization_501c_type character varying(10),
    book_value_assets_eoy bigint,
    total_ubti_computed bigint,
    total_ubti bigint,
    taxable_corporation bigint,
    total_tax_computation bigint,
    total_tax bigint,
    estimated_tax_payments bigint,
    specific_deduction bigint,
    total_deduction bigint,
    charitable_contributions_ded bigint,
    capital_gain_net_income bigint,
    total_ordinary_gain_loss bigint,
    total_prtshp_scorp_income bigint,
    other_income bigint,
    interest_deduction bigint,
    other_deductions bigint,
    total_deductions bigint,
    unrelated_bus_income bigint,
    principal_business_activity_cd character varying(20),
    trade_or_business_desc text,
    source_file character varying(255),
    xml_path character varying(500),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.form990t_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.form990t_details_id_seq OWNED BY public.form990t_details.id;

CREATE TABLE IF NOT EXISTS public.pub78_eligible (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    org_name character varying(500) NOT NULL,
    city character varying(100),
    state character varying(10),
    is_deductible boolean DEFAULT true,
    source_file character varying(255),
    downloaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.revoked_organizations (
    id integer NOT NULL,
    ein character varying(20) NOT NULL,
    org_name character varying(500),
    revocation_date date,
    revocation_reason character varying(255),
    source_file character varying(255),
    downloaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.political_orgs_527 (
    id integer NOT NULL,
    ein character varying(20),
    org_name character varying(500),
    filing_type character varying(10),
    org_type text,
    address character varying(500),
    city character varying(100),
    state character varying(10),
    zip character varying(20),
    filing_date date,
    latitude numeric,
    longitude numeric,
    geocode_date timestamp without time zone,
    geocoding_source character varying(50),
    source_file character varying(255),
    geocoder_match character varying(100),
    geocoder_score numeric(5,2),
    geom_point public.geometry(Point,4326)
);

CREATE SEQUENCE IF NOT EXISTS public.political_orgs_527_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.political_orgs_527_id_seq OWNED BY public.political_orgs_527.id;

CREATE SEQUENCE IF NOT EXISTS public.pub78_eligible_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.pub78_eligible_id_seq OWNED BY public.pub78_eligible.id;

CREATE SEQUENCE IF NOT EXISTS public.revoked_organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.revoked_organizations_id_seq OWNED BY public.revoked_organizations.id;

ALTER TABLE ONLY public.bmf_organization_snapshots ALTER COLUMN id SET DEFAULT nextval('public.bmf_organization_snapshots_id_seq'::regclass);

ALTER TABLE ONLY public.bmf_organizations ALTER COLUMN id SET DEFAULT nextval('public.bmf_organizations_id_seq'::regclass);

ALTER TABLE ONLY public.census_demographics ALTER COLUMN id SET DEFAULT nextval('public.census_demographics_id_seq'::regclass);

ALTER TABLE ONLY public.form990_details ALTER COLUMN id SET DEFAULT nextval('public.form990_details_id_seq'::regclass);

ALTER TABLE ONLY public.form990_schedule_o ALTER COLUMN id SET DEFAULT nextval('public.form990_schedule_o_id_seq'::regclass);

ALTER TABLE ONLY public.form990_soi ALTER COLUMN id SET DEFAULT nextval('public.form990_soi_id_seq'::regclass);

ALTER TABLE ONLY public.form990_soi_private_foundation ALTER COLUMN id SET DEFAULT nextval('public.form990_soi_private_foundation_id_seq'::regclass);

ALTER TABLE ONLY public.form990_xml_import_log ALTER COLUMN id SET DEFAULT nextval('public.form990_xml_import_log_id_seq'::regclass);

ALTER TABLE ONLY public.form990n_small_orgs ALTER COLUMN id SET DEFAULT nextval('public.form990n_small_orgs_id_seq'::regclass);

ALTER TABLE ONLY public.form990t_details ALTER COLUMN id SET DEFAULT nextval('public.form990t_details_id_seq'::regclass);

ALTER TABLE ONLY public.political_orgs_527 ALTER COLUMN id SET DEFAULT nextval('public.political_orgs_527_id_seq'::regclass);

ALTER TABLE ONLY public.pub78_eligible ALTER COLUMN id SET DEFAULT nextval('public.pub78_eligible_id_seq'::regclass);

ALTER TABLE ONLY public.revoked_organizations ALTER COLUMN id SET DEFAULT nextval('public.revoked_organizations_id_seq'::regclass);
