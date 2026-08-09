# USAspending structural drift — resolution record

Date: 2026-08-09
Reference: `usaspending_db` (live, restored from the January 2026 full archive)
Candidate: `usaspending_bdp_validate` (built by this pipeline from the July 2026 subset archive)

The first structural comparison returned **FAIL** with seven classes of drift. Each
one is resolved below. A structural difference is never dismissed: it is either a
defect in this pipeline, a change made by hand in production that was never written
back to source, or a change upstream made between archive vintages. All three
outcomes are recorded, but only the first two produce a code change.

## Summary

| #   | Drift                                                        | Cause                          | Resolution           |
| --- | ------------------------------------------------------------ | ------------------------------ | -------------------- |
| 1   | 5 relations only in candidate                                | upstream vintage               | annotated, no change |
| 2   | `all_entities.latitude/longitude` numeric → double precision | pipeline defect                | fixed                |
| 3   | `mv_entity_spending_summary.latitude/longitude`              | inherited from #2              | fixed by #2          |
| 4   | `recipient_geocode_index` numeric(10,8) → numeric(10,7)      | pipeline defect                | fixed                |
| 5   | `prime_awards.last_modified_date` date → timestamptz         | upstream vintage               | annotated, no change |
| 6   | `update_geom_point_trigger` only in reference                | undocumented production object | recovered            |
| 7   | staging table indexes only in candidate                      | intended                       | annotated, no change |

---

## 1. Five relations present only in the candidate

`public.ai_model`, `public.message`, `public.prompts`, `public.session`,
`public.tool_use`.

All five are owned by `etl_user`, carry zero rows, are absent from the January 2026
full archive, and are present in the July 2026 subset archive. Upstream added them
between vintages.

Not benthic-created and not a pipeline defect. They will appear in the serving
database on the next full restore. No change.

## 2. `all_entities.latitude` and `longitude`: numeric → double precision

`31_all_entities.sql`, extracted verbatim from `build_entity_awards.py` at commit
`c4dd142`, selected these columns as:

```sql
rgi.latitude::double precision,
rgi.longitude::double precision,
```

`pg_get_viewdef` on the live matview shows no cast — the production object carries
bare `numeric`. The cast exists in the ETL source but was never in the deployed
object, which means the live matview was built from a different revision of that
query, or built by hand.

The cast is lossy: `recipient_geocode_index.latitude` is `NUMERIC(10,8)`, and
routing it through a float discards precision the geocoder produced. `numeric` is
canonical.

**Fixed** — cast removed, with a comment recording why.

## 3. `mv_entity_spending_summary.latitude` and `longitude`

This matview selects `e.latitude, e.longitude` straight from `all_entities` with no
cast of its own, in both the live object and `recovered/usaspending/mv_entity_spending_summary.sql`.
The drift was entirely inherited from #2.

**Fixed by #2** — no separate change.

## 4. `recipient_geocode_index` precision

The candidate declared `NUMERIC(10,7)` / `NUMERIC(11,7)`; the reference carries
`NUMERIC(10,8)` / `NUMERIC(11,8)`.

Scale 8 is the convention across every serving database:

| Database         | Relation                  | latitude      | longitude     |
| ---------------- | ------------------------- | ------------- | ------------- |
| `usaspending_db` | `recipient_geocode_index` | numeric(10,8) | numeric(11,8) |
| `usaspending_db` | `rpt.recipient_lookup`    | numeric       | numeric       |
| `irs_ng`         | `bmf_organizations`       | numeric(10,8) | numeric(11,8) |

Scale 7 resolves to roughly 11 mm and scale 8 to roughly 1.1 mm. The difference is
immaterial for address geocoding, but the candidate was silently narrowing a column
relative to production, and a migration that quietly drops a decimal digit is not a
migration anyone should trust.

**Fixed** — `geocode.GEOCODE_COLUMNS_SQL` and the `recipient_geocode_index` DDL in
`pipelines/usaspending/pipeline.py` both now declare scale 8.

## 5. `prime_awards.last_modified_date`: date → timestamptz

`prime_awards` passes this column through from `rpt.award_search` without
transformation. The type differs at the source:

| Archive vintage     | `rpt.award_search.last_modified_date` |
| ------------------- | ------------------------------------- |
| January 2026 (full) | `date`                                |
| July 2026 (subset)  | `timestamp with time zone`            |

An upstream schema change. Not a pipeline defect, and not something to correct —
forcing the old type would misrepresent the data. It resolves itself when the
serving database is restored from a current archive.

Annotated, no change.

## 6. `update_geom_point_trigger` — thirteenth recovered object

Present in the live database, created by no ETL script:

```sql
CREATE FUNCTION public.update_geom_point_trigger() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom_point := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trig_update_geom_point
    BEFORE INSERT OR UPDATE OF latitude, longitude
    ON public.recipient_geocode_index
    FOR EACH ROW EXECUTE FUNCTION update_geom_point_trigger();
```

This pipeline computes `geom_point` explicitly in `geocode.write_results`, so the
trigger is redundant for pipeline writes. It is not redundant for anything else: it
is the only thing keeping `geom_point` consistent when a row is corrected by hand in
`psql`, which is exactly how the column drifts in practice.

**Recovered** to `recovered/usaspending/geom_point_trigger.sql` and applied in
`03_schema`.

## 7. Staging table indexes present only in the candidate

`_staging_award_agg.idx_staging_award_agg_hash` and
`_staging_subaward_agg.idx_staging_subaward_agg_uei`.

These exist because the candidate deliberately retains the staging tables. The
trailing `DROP TABLE ... CASCADE` statements in `build_entity_awards.py` could never
succeed — `all_entities` selects from all three staging tables, so the cascade would
destroy the matview it had just built. That is why the staging tables are still
present in the live database years later.

The pipeline now drops and rebuilds them at the top of `31_all_entities.sql`
instead, which makes the file re-runnable and keeps the lineage intermediates
available for inspection.

Intended behaviour. Annotated, no change.

---

## Indexes present only in the reference

Two indexes exist live with no counterpart in the candidate:

- `public.financial_accounts_by_awards.idx_fabaward_distinct_award_key`
- `public.recipient_geocode_index.idx_rgi_geom_point`

Both are already captured in `recovered/usaspending/indexes_recovered.sql` and
`indexes_derived.sql`. Their absence from the candidate is a consequence of the
validation run predating the index split, not a missing definition. The next
validation run applies them.

## Grants

554 grants appear only in the reference and 520 only in the candidate, with zero
changed. This is not drift in any meaningful sense: the reference has accumulated
per-relation grants across five years of manual administration, while the candidate
grants exactly the nine curated relations named in `08_expose`. The candidate's
grant surface is the one the manifest declares. The reference's is wider than
anything published.

Reconciling this is the point of the migration, not a precondition for it.
