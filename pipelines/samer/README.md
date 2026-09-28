# samer — SAM.gov entity registrations

## At a glance

|                          |                                                                          |
| ------------------------ | ------------------------------------------------------------------------ |
| Dataset                  | `samer`                                                                  |
| Serving database         | `sam_er`                                                                 |
| Source                   | SAM.gov monthly public extract (Entity Management API v4)                |
| Endpoint                 | <https://benthic.io/ngopen/samer/>                                       |
| Manifest                 | <https://benthic.io/bdp/ngopen/samer/manifest.json>                      |
| Documentation            | <https://benthic.io/docs/samer/>                                         |
| Migration status         | `migrated` 2026-08-11, commit `66f5855`                                  |
| Suggested cadence        | monthly                                                                  |
| Archives / restored size | ~1.6 GB / ~6 GB                                                          |
| Extensions               | `postgis`, `pg_trgm`                                                     |
| Replaces                 | `ngopen/gov_to_pg.py`, `ngopen/sam_pipeline.py`, `ngopen/geocode_sam.py` |

## Source

The monthly public extract: pipe-delimited `.dat` files with **142 positional
fields**. This is the only dataset in the collection that is not an archive
download, a git checkout, or a REST API.

Two ways in, in this order:

1. A local extract already in `<archives>/samer/` is used, newest wins. A
   rerun short-circuits here and does no network work.
2. Otherwise `SAM_API_KEY` is required. Without it the stage fails with the
   exact filename and destination directory to place by hand:

```bash
export SAM_API_KEY=...   # sam.gov -> Account Details -> Public API Key
```

The key is read from the environment only. It is never in `ngopen.toml`.

## What each stage does

| Stage        | What actually happens here                                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `00_acquire` | Uses the newest local extract, or requests one via the API: async extract request → poll → download.                                                                      |
| `01_verify`  | Confirms the `.dat` is present and that its field count matches the expected 142. A truncated SAM.gov download is the common failure and it is silent without this check. |
| `02_restore` | **No-op** as a dump restore — the source is a flat file. Parses the `.dat` and upserts into `public.sam_registrations` in `BATCH`-sized batches.                          |
| `03_schema`  | Creates `postgis` and `pg_trgm`, then `sql/10_schema.sql` and `sql/15_keys.sql`.                                                                                          |
| `04_index`   | `sql/20_constraints.sql`, then `recovered/samer/indexes_recovered.sql`.                                                                                                   |
| `05_geocode` | Geocodes `sam_registrations`, resumable by row-id high-water mark keyed on `CURSOR_KEY = "sam_registrations"`.                                                            |
| `06_derive`  | `sql/30_derive.sql`, then `REFRESH MATERIALIZED VIEW public.mv_contractor_registry`, then `sql/25_derived_indexes.sql` and `recovered/samer/indexes_derived.sql`.         |
| `07_analyze` | Plain `ANALYZE;`.                                                                                                                                                         |
| `08_expose`  | Grants `SELECT` on `sam_registrations` and `mv_contractor_registry` to `api_user`.                                                                                        |

## Relations

| Relation                 | Kind              | Notes                                                                                                                         |
| ------------------------ | ----------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `sam_registrations`      | table             | 2,597,460 rows in the 2026-08-09 candidate; the serving database held 856,290 — a +203% delta explained in Verification below |
| `mv_contractor_registry` | materialized view | 866,796 rows                                                                                                                  |

## Recovered objects

This dataset has no recovered materialized views or functions. It does have two
recovered index sets:

| File                    | Contents                                                      |
| ----------------------- | ------------------------------------------------------------- |
| `indexes_recovered.sql` | 16 indexes present only in the live catalog                   |
| `indexes_derived.sql`   | indexes named in a legacy script but missing from the catalog |

`mv_contractor_registry` is coded, not recovered — it has a source in
`sql/30_derive.sql`.

## Gotchas

**`FIELD_MAP` is positional and must not be tidied.** The indices below are the
contract with SAM.gov's 142-field layout, carried over verbatim from the legacy
`gov_to_pg.py`. Mailing address is _not_ contiguous — city 41, zip 42, country
44, state 45 — and `naics_codes` (31) precedes `primary_naics` (32) rather than
following it. Re-sorting this dict to "read better" will silently corrupt every
address in the table.

**`mv_contractor_registry` is a view over a single-table database.** The public
docs page says "this is a single-table database" in one place and then documents
this materialized view in another. Both are true: there is one base table, one
view over it. That is not a contradiction, but it reads like one.

**Geocoding writes the shared contract, not the legacy columns.** The legacy
`geocode_sam.py` stored bare `latitude`/`longitude` numerics and a
`geocoding_source` column. The shared geocoder in `ngopen_bdp.geocode` writes
the protocol-wide column set. Both coexist in the serving database; see
[`irs_ng`](../irs_ng/README.md) for the same situation.

**No RPC functions are published.** `rpc/st_dwithin` exists as a PostGIS path in
the database but is deliberately not part of the published contract, and the
generated OpenAPI spec strips it.

## Verification

```bash
ngopen status samer
ngopen compare samer --right sam_er_bdp_next
```

The 2026-08-09 comparison at
[`../audit/samer-structural-2026-08-09.md`](../audit/samer-structural-2026-08-09.md)
reports **0 differences** in relations, columns, indexes, constraints, functions
and geometry. The only structural difference is one grant the candidate has and
the reference does not: `sam_registrations.api_user.SELECT`.

The +1,741,170 row delta on `sam_registrations` is **not a regression**. The
live `sam_er` had been built against an older monthly extract; the candidate
pulls the current one. This is the distinction `ngopen compare` draws between
its structural gate and its advisory content section — see
[MIGRATE.md](../MIGRATE.md).

## Related

- [Repository README](../README.md) — the collection and the stage contract
- [MIGRATE.md](../MIGRATE.md) — moving a live dataset onto pipeline-built relations
- <https://benthic.io/docs/samer/> — the public API reference
- <https://benthic.io/apis/> — how `samer` joins to `usaspending` and `irs_ng`
