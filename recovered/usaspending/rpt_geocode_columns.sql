-- RECOVERED DDL
-- provenance: recovered
--
-- rpt.recipient_lookup carries four geocoding columns that no ngopen script
-- adds. geocode_usas.py writes its results to public.recipient_geocode_index
-- instead, so these were added by hand in psql and are otherwise undocumented.
-- Extracted from information_schema on 2026-08-08.
--
-- database: usaspending_db
-- object:   rpt.recipient_lookup (columns)
-- kind:     table alteration

ALTER TABLE rpt.recipient_lookup
    ADD COLUMN IF NOT EXISTS latitude       numeric,
    ADD COLUMN IF NOT EXISTS longitude      numeric,
    ADD COLUMN IF NOT EXISTS geocode_date   timestamptz,
    ADD COLUMN IF NOT EXISTS geocode_system varchar(50);
