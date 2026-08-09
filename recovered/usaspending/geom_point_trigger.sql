-- RECOVERED DDL
-- database: usaspending_db
-- object:   public.update_geom_point_trigger() + trigger trig_update_geom_point
-- kind:     function, trigger
-- provenance: recovered
--
-- Extracted verbatim from the live catalog on 2026-08-09. No ETL script in the
-- legacy ngopen tree creates either object; both were applied by hand in psql.
--
-- The trigger keeps geom_point synchronised with latitude/longitude on
-- public.recipient_geocode_index. The BDP pipeline computes geom_point
-- explicitly in ngopen_bdp.geocode.write_results, so the trigger is redundant
-- for pipeline-driven writes -- but it is the only thing protecting the
-- invariant against manual UPDATEs, and it is part of the live structure, so
-- it is reproduced here for structural fidelity.

CREATE OR REPLACE FUNCTION public.update_geom_point_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom_point := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS trig_update_geom_point ON public.recipient_geocode_index;

CREATE TRIGGER trig_update_geom_point
    BEFORE INSERT OR UPDATE OF latitude, longitude
    ON public.recipient_geocode_index
    FOR EACH ROW
    EXECUTE FUNCTION public.update_geom_point_trigger();
