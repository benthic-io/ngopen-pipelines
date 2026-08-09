-- RECOVERED DDL
-- provenance: recovered
--
-- Extensions installed in usaspending_db that appear neither in the upstream
-- pg_dump archive's requirements nor in any ngopen script. Added by hand.
--
-- database: usaspending_db
-- kind:     extensions

CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
