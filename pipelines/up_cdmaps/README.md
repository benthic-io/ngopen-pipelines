# up_cdmaps — historical congressional district boundaries

## At a glance

|                          |                                                            |
| ------------------------ | ---------------------------------------------------------- |
| Dataset                  | `up_cdmaps`                                                |
| Serving database         | `ucla_polysci_cdmaps`                                      |
| Source                   | [UCLA PolySci CDMaps](https://cdmaps.polisci.ucla.edu/shp) |
| Endpoint                 | <https://benthic.io/ngopen/up_cdmaps/>                     |
| Manifest                 | <https://benthic.io/bdp/ngopen/up_cdmaps/manifest.json>    |
| Documentation            | <https://benthic.io/docs/up_cdmaps/>                       |
| Migration status         | `migrated` 2026-08-11, commit `66f5855`                    |
| Suggested cadence        | **never** — static historical reference, run once          |
| Archives / restored size | ~2.8 GB / ~4.5 GB                                          |
| Extensions               | `postgis`                                                  |
| Replaces                 | `ngopen/ucla_cd_to_pg.py`                                  |

## Source

119 district shapefile archives, one per Congress from 1 to 119, fetched from
`[sources.up_cdmaps].base_url`. The range is configured, not hardcoded:

```toml
[sources.up_cdmaps]
base_url       = "https://cdmaps.polisci.ucla.edu/shp"
congress_range = [1, 119]
source_srid    = 4269
target_srid    = 3857
```

Each archive is hashed on download, and ingest stages skip any input whose hash
has already been loaded. This is the only dataset here where a rerun does
essentially nothing, which is the correct behaviour: the source does not change.

## What each stage does

| Stage        | What actually happens here                                                                                                                                                       |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `00_acquire` | Downloads each Congress archive in `congress_range`. Resumable by byte offset.                                                                                                   |
| `01_verify`  | Confirms every archive in the range is present and is a readable zip.                                                                                                            |
| `02_restore` | **No-op.** The source is shapefiles read with `geopandas`/`shapely`, not a `pg_restore` dump. Returns `skipped`.                                                                 |
| `03_schema`  | Creates `postgis`, then `sql/10_schema.sql` and `sql/15_keys.sql`.                                                                                                               |
| `04_index`   | `sql/20_constraints.sql`, then `recovered/up_cdmaps/indexes_recovered.sql`. This dataset has **no** `25_derived_indexes.sql` — it is the only one of the five without that file. |
| `05_geocode` | **Skipped.** Boundaries are not addresses. Returns `skipped`.                                                                                                                    |
| `06_derive`  | `sql/30_derive.sql`, plus the two recovered RPCs.                                                                                                                                |
| `07_analyze` | Plain `ANALYZE;`.                                                                                                                                                                |
| `08_expose`  | Grants on `congressional_districts` and `EXECUTE` on both RPCs.                                                                                                                  |

## Relations

One table and two functions — the smallest exposed surface in the collection.

| Relation                  | Kind     | Notes                                  |
| ------------------------- | -------- | -------------------------------------- |
| `congressional_districts` | table    | 39,297 rows as of the 2026-08-09 build |
| `rpc_find_district`       | function | **recovered**; point-in-polygon lookup |
| `rpc_districts_in_bbox`   | function | **recovered**; bounding-box query      |

## Recovered objects

| File                        | Object                                                                                                          |
| --------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `rpc_find_district.sql`     | `public.rpc_find_district(double precision, double precision, integer)`                                         |
| `rpc_districts_in_bbox.sql` | `public.rpc_districts_in_bbox(double precision, double precision, double precision, double precision, integer)` |
| `indexes_recovered.sql`     | 5 indexes present only in the live catalog                                                                      |

Both functions were created by hand in `psql` and never written down. They are
`provenance: "recovered"` in the manifest.

## Gotchas

**This is the one dataset that cannot be spatially joined to the others without
an explicit transform.** Geometry is stored in **EPSG:3857** (Web Mercator) to
match the existing serving database. Every other spatial dataset in the
collection — and every upstream source — is EPSG:4326. The source shapefiles
here are EPSG:4269 (NAD83), and the reprojection to 3857 is declared in the
BDP manifest. A naive `ST_Intersects` between this table and an `irs_ng`
point will return wrong answers, and it will do so silently. This is called out
on the public docs page for the same reason.

**Districts with no shape are kept.** Some Congresses have a boundary entry
with null geometry rather than no entry at all. Dropping them would lose the
record that the district existed; they are retained with a null `geom`.

**3857 makes this table the collection's biggest single relation.** At ~4.5 GB
it is comparable to `samer` in its entirety, and it is static. If you are
short on disk, this is the one dataset you do not need to re-fetch.

**The two RPCs are the entire spatial API.** There is no PostGIS function
exposed for generic geometry queries — clients must use `rpc_find_district` or
`rpc_districts_in_bbox`. The public docs page documents both twice, in
different sections; the parameter tables in the "Spatial RPC Functions" section
are the authoritative ones.

## Verification

```bash
ngopen status up_cdmaps
ngopen compare up_cdmaps --right ucla_polysci_cdmaps_bdp_next --no-content
```

The 2026-08-09 comparison at
[`../audit/up_cdmaps-structural-2026-08-09.md`](../audit/up_cdmaps-structural-2026-08-09.md)
is the cleanest in the collection: **0 differences in every structural aspect**
except the same 6 PostGIS catalog grants (`geography_columns`, `geometry_columns`,
`spatial_ref_sys` to `api_user` and `web_anon`) that a fresh `postgis` install
does not produce.

## Related

- [Repository README](../README.md) — the collection and the stage contract
- [usp_cl](../usp_cl/README.md) — resolves districts by `state` + `district`, not geometry
- [MIGRATE.md](../MIGRATE.md) — moving a live dataset onto pipeline-built relations
- <https://benthic.io/docs/up_cdmaps/> — the public API reference
