# irs_ng — IRS nonprofit filings

## At a glance

|                          |                                                                             |
| ------------------------ | --------------------------------------------------------------------------- |
| Dataset                  | `irs_ng`                                                                    |
| Serving database         | `irs_ng`                                                                    |
| Source                   | IRS BMF, Form 990 XML, 990-T, 990-N, Pub 78, revocations, 527s, Census ACS5 |
| Endpoint                 | <https://benthic.io/ngopen/irs_ng/>                                         |
| Manifest                 | <https://benthic.io/bdp/ngopen/irs_ng/manifest.json>                        |
| Documentation            | <https://benthic.io/docs/irs_ng/>                                           |
| Migration status         | `migrated` 2026-08-14, commit `66f5855`                                     |
| Suggested cadence        | monthly (cadence varies by feed)                                            |
| Archives / restored size | ~35 GB / ~40 GB                                                             |
| Extensions               | `postgis`, `pg_trgm`, `dblink`                                              |
| Replaces                 | `ngopen/irs_ng.py`                                                          |

## Source

Seven distinct feeds, declared in `pipelines/irs_ng/irs_urls.json` rather than
scattered through the code:

| Key          | What it is                                    | Cadence  |
| ------------ | --------------------------------------------- | -------- |
| `bmf`        | Business Master File from NCCS S3             | monthly  |
| `soi`        | 990-SOI bulk extracts, EO and EZ zips         | annual   |
| `xml`        | e-Postcard 990 XML, one zip per year per part | annual   |
| `pub78`      | Pub 78 auto-revocation list                   | static   |
| `revocation` | Revoked organization list                     | static   |
| `form990n`   | 990-N small organization returns              | periodic |
| `527`        | Political organization 527 filings            | rolling  |

Plus Census ACS5 for `census_demographics`, configured in `ngopen.toml`:

```toml
[sources.irs_ng]
url_registry = "pipelines/irs_ng/irs_urls.json"
census_api   = "https://api.census.gov/data"
census_years = [2023]
```

`CENSUS_API_KEY` is **not required**. ACS5 serves unauthenticated requests
below roughly 500 per day per IP, which is enough for this dataset. A key
raises that ceiling; it is never needed to make a build work.

## What each stage does

| Stage        | What actually happens here                                                                                                                                                                           |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `00_acquire` | Fetches every feed in the registry plus the Census extract. Resumable by byte offset.                                                                                                                |
| `01_verify`  | Validates each artifact against its registry entry.                                                                                                                                                  |
| `02_restore` | Delegates to `legacy_import.py` — carried over verbatim from the legacy monolith. COPY-based BMF import, per-file snapshots removed.                                                                 |
| `03_schema`  | Creates `postgis`, `pg_trgm`, `dblink`, then `sql/10_schema.sql` and `sql/15_keys.sql`.                                                                                                              |
| `04_index`   | `sql/20_constraints.sql`, then `recovered/irs_ng/indexes_recovered.sql`.                                                                                                                             |
| `05_geocode` | Geocodes `public.bmf_organizations` and `public.political_orgs_527` — the only two relations with mappable addresses. `CURSOR_KEY` is not used; the cursor is per-table.                             |
| `06_derive`  | `sql/30_derive.sql`, which declares every matview `WITH NO DATA` so the DDL stays cheap, then a `REFRESH` per matview, then `sql/25_derived_indexes.sql` and `recovered/irs_ng/indexes_derived.sql`. |
| `07_analyze` | Plain `ANALYZE;`.                                                                                                                                                                                    |
| `08_expose`  | Grants `SELECT` on the 18 relations in `EXPOSED` to `api_user`.                                                                                                                                      |

`06_derive` is where the recovered objects are created; they are listed under
[Recovered objects](#recovered-objects) below.

## Relations

Eighteen relations are exposed. The largest surface in the collection.

| Relation                         | Kind                              |
| -------------------------------- | --------------------------------- |
| `bmf_organizations`              | table                             |
| `bmf_organization_snapshots`     | table                             |
| `census_demographics`            | table                             |
| `form990_details`                | table                             |
| `form990_schedule_o`             | table                             |
| `form990_soi`                    | table                             |
| `form990_soi_private_foundation` | table                             |
| `form990_xml_import_log`         | table                             |
| `form990n_small_orgs`            | table                             |
| `form990t_details`               | table                             |
| `political_orgs_527`             | table                             |
| `pub78_eligible`                 | table                             |
| `revoked_organizations`          | table                             |
| `mv_nonprofit_profile`           | materialized view — **recovered** |
| `mv_org_financial_health`        | materialized view — **recovered** |
| `v_org_financial_profile`        | view                              |
| `v_org_multi_year`               | view                              |
| `v_political_orgs`               | view                              |

Plus two recovered spatial RPCs, `rpc_nonprofits_in_district` and
`rpc_nonprofits_nearby`, exposed for PostgREST `POST`.

## Recovered objects

This dataset has the most recovered objects in the collection: **four**
hand-built database objects, plus two index sets. All four existed in the live
`irs_ng` catalog, were reachable over PostgREST, and had no source anywhere.
They were extracted from `pg_get_viewdef` / `pg_get_functiondef` and are
labelled `provenance: "recovered"` in the manifest.

| File                             | Object                                      | Kind              |
| -------------------------------- | ------------------------------------------- | ----------------- |
| `mv_nonprofit_profile.sql`       | `public.mv_nonprofit_profile`               | materialized view |
| `mv_org_financial_health.sql`    | `public.mv_org_financial_health`            | materialized view |
| `rpc_nonprofits_in_district.sql` | `public.rpc_nonprofits_in_district`         | function          |
| `rpc_nonprofits_nearby.sql`      | `public.rpc_nonprofits_nearby`              | function          |
| `indexes_recovered.sql`          | 56 indexes present only in the live catalog | indexes           |
| `indexes_derived.sql`            | indexes on the recovered matviews           | indexes           |

The two RPCs are the collection's nonprofit geospatial API: point-in-district
and radius search. Both do an explicit `ST_Transform` from 4326 to 3857 on both
sides of `ST_DWithin` and `ST_Distance`, rather than depending on `earth_box`
or `cube`. Both were applied by hand in `psql`.

## Gotchas

**The legacy importer is still the loader.** `legacy_import.py` is carried
over verbatim rather than rewritten. `pipeline.py` is the thin stage layer
that sequences it. This is deliberate: the ingest is the part most likely to
be subtly wrong, and it has been exercised against real multi-day runs. If you
are changing behaviour, change the stage layer first and treat the importer as
frozen unless you have a live database to test against.

**Two geocoding column sets coexist.** The legacy importer stored lat/lon as
bare `numeric` with a `geocoding_source` column. The shared geocoder in
`ngopen_bdp.geocode` writes the protocol-wide contract. Both are present in the
serving database, and a migration has to carry the legacy values across — which
is what `geocode.preserve()` does. See
[MIGRATE.md](../MIGRATE.md).

**`GEOCODE_TABLES` is two relations, not thirteen.** Only
`bmf_organizations` and `political_orgs_527` carry a mappable address. The Form
990 tables have no address columns at all.

**Matviews are declared `WITH NO DATA`.** `30_derive.sql` creates every matview
empty and `06_derive` refreshes them in a separate step. Without this a build
would pay the matview population cost twice.

## Verification

```bash
ngopen status irs_ng
ngopen compare irs_ng --right irs_ng_v4 --no-content
```

The most recent comparison, 2026-09-21, is at
[`../audit/irs_ng-structural-2026-09-21.md`](../audit/irs_ng-structural-2026-09-21.md).
It reports **0 differences** in relations, columns, indexes, constraints,
functions and geometry — the closest of the five to structural equivalence. The
only difference is 16 grants the candidate has and the reference lacks, all
`api_user.SELECT` on exposed relations. Those were applied by hand to the
serving database and never written back to source.

## Related

- [Repository README](../README.md) — the collection and the stage contract
- [MIGRATE.md](../MIGRATE.md) — moving a live dataset onto pipeline-built relations
- [samer](../samer/README.md) — the other contractor-facing dataset, and the only one that needs `SAM_API_KEY`
- <https://benthic.io/docs/irs_ng/> — the public API reference
