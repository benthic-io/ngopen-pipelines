# usp_cl — U.S. legislators, committees, and district offices

## At a glance

|                          |                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------- |
| Dataset                  | `usp_cl`                                                                                    |
| Serving database         | `us_project_cl`                                                                             |
| Source                   | [`unitedstates/congress-legislators`](https://github.com/unitedstates/congress-legislators) |
| Endpoint                 | <https://benthic.io/ngopen/usp_cl/>                                                         |
| Manifest                 | <https://benthic.io/bdp/ngopen/usp_cl/manifest.json>                                        |
| Documentation            | <https://benthic.io/docs/usp_cl/>                                                           |
| Migration status         | `migrated` 2026-08-11, commit `66f5855`                                                     |
| Suggested cadence        | weekly (continuous git source)                                                              |
| Archives / restored size | ~11 MB / ~40 MB                                                                             |
| Extensions               | `postgis`, `pg_trgm`                                                                        |
| Replaces                 | `ngopen/us_project_to_pg.py`                                                                |

## Source

A git checkout, not a downloadable archive. `00_acquire` clones on first run
and fast-forwards thereafter, then records the resolved commit so a manifest
names the exact upstream revision the data came from.

`congress_range` is not a config key here — this pipeline always reads the whole
repository. `up_cdmaps` is the dataset with a range.

Eight YAML documents are consumed, in this load order:

1. `legislators-historical.yaml`
2. `legislators-current.yaml`
3. `legislators-social-media.yaml`
4. `legislators-district-offices.yaml`
5. `committees-historical.yaml`
6. `committees-current.yaml`
7. `committee-membership-current.yaml`
8. `executive.yaml`

## What each stage does

| Stage        | What actually happens here                                                                                                                                                   |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `00_acquire` | `git clone` or `git fetch --depth` + fast-forward into `<archives>/usp_cl/congress-legislators`; records the commit SHA.                                                     |
| `01_verify`  | Confirms all eight YAML files are present and parseable. A missing document is an error, not a warning — a silent partial load would look like a real shrinkage in the data. |
| `02_restore` | **No-op.** There is nothing to restore: the source is YAML parsed in-process. Returns `skipped`.                                                                             |
| `03_schema`  | Creates `postgis` and `pg_trgm`, then `sql/10_schema.sql` and `sql/15_keys.sql`.                                                                                             |
| `04_index`   | `sql/20_constraints.sql`, then `recovered/usp_cl/indexes_recovered.sql`.                                                                                                     |
| `05_geocode` | Geocodes `district_offices` only. Other tables carry no mappable address. Resumable by row-id high-water mark keyed on `CURSOR_KEY = "district_offices"`.                    |
| `06_derive`  | `sql/30_derive.sql`, then `REFRESH MATERIALIZED VIEW` on both matviews, then — and only then — `sql/25_derived_indexes.sql` and `recovered/usp_cl/indexes_derived.sql`.      |
| `07_analyze` | Plain `ANALYZE;`.                                                                                                                                                            |
| `08_expose`  | Grants `SELECT` on the 12 relations in `EXPOSED` to `api_user` and `web_anon`.                                                                                               |

`sql/16_natural_keys.sql` is unique to this dataset. Seven relations have no
surrogate key that distinguishes rows reliably across a refresh, so a unique
constraint on the natural key is what makes the upsert in `02_restore` a no-op
instead of a duplicate source:

`committee_membership`, `committees`, `district_offices`, `executive_terms`,
`legislator_other_names`, `legislator_social_media`, `legislator_terms`,
`subcommittees`.

## Relations

Twelve relations are exposed. Ten tables, two materialized views.

| Relation                  | Kind              | Notes                                   |
| ------------------------- | ----------------- | --------------------------------------- |
| `legislators`             | table             | 12,768 rows as of the 2026-08-09 build  |
| `legislator_terms`        | table             | 45,533 rows; the largest relation here  |
| `legislator_other_names`  | table             | 5 rows; tiny, but carries a natural key |
| `legislator_social_media` | table             | 518 rows                                |
| `district_offices`        | table             | 1,306 rows; the geocoded relation       |
| `committees`              | table             | 76 rows                                 |
| `subcommittees`           | table             | 200 rows                                |
| `committee_membership`    | table             | 3,891 rows                              |
| `executives`              | table             | 67 rows                                 |
| `executive_terms`         | table             | 107 rows                                |
| `mv_current_lawmakers`    | materialized view | **recovered**                           |
| `mv_committee_power`      | materialized view | **recovered**                           |

No RPC functions. Spatially, this dataset is joined to `up_cdmaps` through
`legislator_terms.state` + `district` rather than through geometry, because
`district_offices.geom_point` is a point and the districts are polygons.

## Recovered objects

Two matviews, extracted from `pg_get_viewdef` on the live `us_project_cl`
catalog and committed under `recovered/usp_cl/`:

| File                       | Object                                                        |
| -------------------------- | ------------------------------------------------------------- |
| `mv_current_lawmakers.sql` | `public.mv_current_lawmakers`                                 |
| `mv_committee_power.sql`   | `public.mv_committee_power`                                   |
| `indexes_recovered.sql`    | 43 indexes present only in the live catalog                   |
| `indexes_derived.sql`      | indexes named in a legacy script but missing from the catalog |

Both matviews existed in production, were reachable over PostgREST, and had no
source anywhere. They are labelled `provenance: "recovered"` in the manifest
rather than `derived`, because calling a hand-built object "derived"
misrepresents where it came from.

## Gotchas

**Congress numbering is not `year // 2`.** `calculate_congress()` implements
the 20th Amendment boundary: before 1935 a Congress started on March 4, after
1935 on January 3. A date of 1935-01-02 belongs to the _previous_ Congress. The
logic is carried verbatim from the legacy importer and must not be "simplified".

**`_first()` exists because of Postgres array literals.** Several upstream YAML
fields are sometimes a scalar and sometimes a list. psycopg2 adapts a Python
list to a Postgres array literal, but JSON-encoding it produces
`'["F000246"]'`, which Postgres rejects because a bracketed array literal must
declare explicit dimensions. Both empty and missing become `NULL` rather than
an empty array, to match the serving database.

**`district_offices` has two extra geocoding columns** — `geocode_date` and
`geocode_system` — that the serving database does not have. They are the
protocol-wide geocoding contract; see `irs_ng` for the same situation, and
[../HOUSE-STYLE.md](../HOUSE-STYLE.md) for why the shared geocoder wins.

**`25_derived_indexes.sql` is applied in `06_derive`, not `04_index`.** Indexes
on a materialized view cannot be created before the view exists, so they are
deliberately held back from the index stage and applied at the end of derive,
after the `REFRESH`. Same for `recovered/usp_cl/indexes_derived.sql`. If you
move them back into `04_index` for tidiness, the build fails.

**Six PostGIS catalog grants are missing from the candidate.** The live
database grants `SELECT` on `geography_columns`, `geometry_columns`, and
`spatial_ref_sys` to `api_user` and `web_anon`; a fresh build does not. This is
the sole structural difference in the 2026-08-09 comparison, and it is the
reason that report's verdict is `FAIL`. See
[MIGRATE.md](../MIGRATE.md) for how grants participate in the gate.

## Verification

```bash
ngopen status usp_cl
ngopen compare usp_cl --right us_project_cl_bdp_next --no-content
```

The 2026-08-09 comparison is preserved at
[`../audit/usp_cl-structural-2026-08-09.md`](../audit/usp_cl-structural-2026-08-09.md).
It records 0 relation differences, 0 column differences beyond the two
geocoding columns above, 8 natural-key indexes and constraints the candidate
adds, and 6 grants it lacks. Content delta on `district_offices` was −6 rows
(−0.5%), consistent with upstream corrections.

## Related

- [Repository README](../README.md) — the collection and the stage contract
- [MIGRATE.md](../MIGRATE.md) — moving a live dataset onto pipeline-built relations
- [AUDIT.md](../AUDIT.md) — provenance history and the recovered-object inventory
- [up_cdmaps](../up_cdmaps/README.md) — the spatial join partner
- <https://benthic.io/docs/usp_cl/> — the public API reference
