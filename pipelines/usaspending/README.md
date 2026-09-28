# usaspending — federal contract and assistance awards

## At a glance

|                          |                                                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| Dataset                  | `usaspending`                                                                                                 |
| Serving database         | `usaspending_db`                                                                                              |
| Source                   | [USAspending.gov bulk archive](https://api.usaspending.gov/api/v2/bulk_download/list_database_download_files) |
| Endpoint                 | <https://benthic.io/ngopen/usaspending/>                                                                      |
| Manifest                 | <https://benthic.io/bdp/ngopen/usaspending/manifest.json>                                                     |
| Documentation            | <https://benthic.io/docs/usaspending/>                                                                        |
| Migration status         | `migrated` 2026-09-21, commit `b25eba8`                                                                       |
| Suggested cadence        | monthly                                                                                                       |
| Archives / restored size | ~164 GB zip + ~130 GB expanded / **~1.1 TB**                                                                  |
| Extensions               | `postgis`, `pg_trgm`, `dblink`, `hstore`, `intarray`, `pg_prewarm`, `pg_stat_statements`, `postgres_fdw`      |
| Replaces                 | `ngopen/geocode_usas.py`, `ngopen/build_entity_awards.py`                                                     |

## Source

Resolved from the upstream bulk-download listing rather than hardcoded:

```toml
[sources.usaspending]
discovery_url = "https://api.usaspending.gov/api/v2/bulk_download/list_database_download_files"
variant       = "full"   # "full" | "subset"
```

`00_acquire` picks `full_download_file` or `subset_download_file` according to
`--variant`, HEADs it, and skips the download if the local artifact is already
current by URL and size. The `full` archive is ~164 GB; `subset` is 4.6 GB and
restores in hours instead of days. **Use `subset` for anything short of a real
regeneration** — see the storage constraints in [../AUDIT.md](../AUDIT.md).

This is the only dataset in the collection that needs a superuser role named
`root`, because the upstream archive's objects are owned by `root`:

```sql
CREATE ROLE root SUPERUSER LOGIN;
```

## What each stage does

| Stage        | What actually happens here                                                                                                                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `00_acquire` | Resolves the archive from the upstream listing, HEADs it, skips if current, otherwise downloads resumably by byte offset (`aria2c` is used automatically over 256 MB).                                                                     |
| `01_verify`  | Checks the expanded dump directory against the archive and records a per-file hash so ingest stages skip what is already loaded.                                                                                                           |
| `02_restore` | **Two-phase `pg_restore`, driven by a TOC split.** The TOC is partitioned into a base list and a materialized-view-data list; phase 1 restores base tables with `--clean --if-exists`, then `ANALYZE`, then phase 2 restores matview data. |
| `03_schema`  | Creates the 8 extensions, grants `etl_user` the `USAGE`/`SELECT` it needs to refresh matviews, then `recovered/usaspending/extensions_recovered.sql`.                                                                                      |
| `04_index`   | `recovered/usaspending/indexes_recovered.sql` — 76 indexes. This dataset has **no** `20_constraints.sql`; constraints arrive with the archive.                                                                                             |
| `05_geocode` | Geocodes the `rpt.recipient_lookup` source, writing `public.recipient_geocode_index`. Resumable by row-id high-water mark, `CURSOR_KEY = "recipient_lookup"`.                                                                              |
| `06_derive`  | Runs `sql/31_all_entities.sql`, `ANALYZE public.all_entities`, then `32_prime_awards_B.sql`, `33_subawards.sql`, `34_entity_awards.sql`; then the three recovered matviews; then `recovered/usaspending/indexes_derived.sql`.              |
| `07_analyze` | Plain `ANALYZE;`.                                                                                                                                                                                                                          |
| `08_expose`  | Grants on the 9 relations in `EXPOSED`.                                                                                                                                                                                                    |

**This dataset is structurally different from the other four.** It is the only
one with no `10_schema.sql`, `15_keys.sql`, or `20_constraints.sql` — the
upstream archive supplies the schema, keys and constraints, so benthic's
`sql/` directory holds only the four derivation scripts that _add_ to it.
`03_schema` and `04_index` are correspondingly thin.

### Path B for `prime_awards`

`32_prime_awards_B.sql` is the canonical build. It aggregates
`rpt.transaction_search` rather than reading `rpt.award_search` alone, because
upstream's "full" archive ships only ~354K rows in `award_search` while
`transaction_search` carries 232M rows covering ~4.44M distinct awards.

The superseded Path A was removed at commit `7413b1b`; it rebuilt
`prime_awards` a second time from `award_search` and cost roughly 25 hours on
full data. Do not reintroduce it.

### Why `ANALYZE` runs inside `06_derive`

`31_all_entities.sql` is followed immediately by `ANALYZE public.all_entities`
because the 240M-row `GROUP BY` and joins that follow need fresh statistics.
Relying on `07_analyze` at the end of derive — or on autovacuum — left the
planner working blind. This is the one place in the collection where a stage
does part of a later stage's job, and it is deliberate.

## Relations

Nine relations are exposed. The database is far larger than this list: it also
carries the upstream `raw`, `int`, and read-only `rpt` schemas, plus ~113
indexes, all of benthic's making — the upstream archive ships zero indexes.

| Relation                     | Kind              | Notes                                                 |
| ---------------------------- | ----------------- | ----------------------------------------------------- |
| `all_entities`               | table             | the entity spine; 28 columns                          |
| `prime_awards`               | table             | Path B build                                          |
| `subawards`                  | table             |                                                       |
| `entity_awards`              | table             | per-award entity join                                 |
| `recipient_geocode_index`    | table             | `NUMERIC(10,8)` lat/lon — `numeric` is canonical here |
| `uei_crosswalk`              | table             | DUNS-to-UEI transition                                |
| `mv_entity_spending_summary` | materialized view | **recovered**                                         |
| `mv_district_spending`       | materialized view | **recovered**                                         |
| `mv_covid_spending`          | materialized view | **recovered**                                         |

## Recovered objects

| File                             | Object                                                          | Kind              |
| -------------------------------- | --------------------------------------------------------------- | ----------------- |
| `mv_entity_spending_summary.sql` | `public.mv_entity_spending_summary`                             | materialized view |
| `mv_district_spending.sql`       | `public.mv_district_spending`                                   | materialized view |
| `mv_covid_spending.sql`          | `public.mv_covid_spending`                                      | materialized view |
| `rpt_geocode_columns.sql`        | 4 geocoding columns on `rpt.recipient_lookup`                   | columns           |
| `geom_point_trigger.sql`         | `public.update_geom_point_trigger()` + `trig_update_geom_point` | function, trigger |
| `extensions_recovered.sql`       | `cube`, `earthdistance`, `fuzzystrmatch`                        | extensions        |
| `indexes_recovered.sql`          | 76 indexes present only in the live catalog                     | indexes           |
| `indexes_derived.sql`            | indexes on the recovered matviews                               | indexes           |

## Gotchas

**A full from-scratch run is not currently possible in place.** It needs
roughly 1.4 TB transiently, and because the existing `usaspending_db` cannot be
dropped until its replacement is proven, a true regeneration needs both
resident — about 2.5 TB. `/raid_0` is 3.7 TB with ~1.2 TB free. This is the
single most important operational constraint in this repository and it lives in
[../AUDIT.md](../AUDIT.md) §5.

**`numeric` is canonical for latitude and longitude, not `double precision`.**
`all_entities.latitude` was declared `double precision` in the ETL source at
commit `c4dd142` but carries bare `numeric` in the deployed object. The cast is
lossy against `recipient_geocode_index.NUMERIC(10,8)`. Fixed, and recorded in
[`../audit/usaspending-drift-resolution.md`](../audit/usaspending-drift-resolution.md) §2.

**`recovered/usaspending/geom_point_trigger.sql` is an undocumented
hand-built object.** `public.update_geom_point_trigger()` and the trigger
`trig_update_geom_point` exist in the serving database, are applied by no
script, and are not in the "twelve recovered objects" table in
[../AUDIT.md](../AUDIT.md) §3. They are recovered here. It was drift class #6
in the resolution record.

**`cube`, `earthdistance`, and `fuzzystrmatch` are installed but unexplained.**
They appear in neither the upstream dump's requirements nor any script. Captured
in `recovered/usaspending/extensions_recovered.sql`.

**The `raw` schema was dropped deliberately.** The 2026-08-09 audit recorded its
structure before removal: upstream pre-transform staging tables, superseded by
their `rpt` counterparts, read by no benthic ETL and not declared queryable in
the manifest. The full structural record is
[`../audit/usaspending-raw-drop.md`](../audit/usaspending-raw-drop.md), kept so
the removal stays auditable.

**`07_analyze` does not refresh the matviews.** `06_derive` does. If you are
looking for the refresh, that is where it is.

## Verification

```bash
ngopen status usaspending
ngopen compare usaspending --left usaspending_db --right usaspending_bdp_next
ngopen run usaspending --variant subset --dbname usaspending_bdp_validate
```

Three reports, in increasing age:

| Report                                                                                  | What it established                                                                                                                           |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| [`usaspending-structural-2026-09-21.md`](../audit/usaspending-structural-2026-09-21.md) | 5 upstream-vintage relations, 36 columns, 241 indexes and 154 constraints the candidate adds; `entity_awards` type changes; 609 vs 588 grants |
| [`usaspending-drift-resolution.md`](../audit/usaspending-drift-resolution.md)           | 7 drift classes, each classified as pipeline defect / undocumented production object / upstream vintage, with the 2 real defects fixed        |
| [`usaspending-structural-2026-08-09.md`](../audit/usaspending-structural-2026-08-09.md) | the original 1321-line comparison against the `subset` validation build                                                                       |

`usaspending_bdp_validate` is a throwaway database built from the 4.6 GB subset
archive and exercised through all nine stages. It never touches the five
serving databases and is retained as a regression fixture.

## Related

- [Repository README](../README.md) — the collection and the stage contract
- [MIGRATE.md](../MIGRATE.md) — moving a live dataset onto pipeline-built relations
- [samer](../samer/README.md) — the join partner, by UEI
- <https://benthic.io/docs/usaspending/> — the public API reference
- <https://benthic.io/apis/> — declared join paths across the collection
