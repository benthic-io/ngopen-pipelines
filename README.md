# ngopen-bdp-pipelines

ETL pipelines for the **NGOpen** collection — five public PostgREST APIs over
U.S. government spending, nonprofit, and legislative data, published at
[benthic.io](https://benthic.io/ngopen/).

Every pipeline runs from scratch in the complete absence of data, refreshes in
place when re-run, and resumes where it left off after a crash. Each publishes
a signed [BDP](https://benthic.io/bdp/) manifest so anyone can verify that the
code in this repository produced the data being served.

---

## The collection

| Dataset       | Database              | Source                            | Endpoint                                                       |
| ------------- | --------------------- | --------------------------------- | -------------------------------------------------------------- |
| `usaspending` | `usaspending_db`      | USAspending.gov bulk archive      | [/ngopen/usaspending/](https://benthic.io/ngopen/usaspending/) |
| `samer`       | `sam_er`              | SAM.gov entity registrations      | [/ngopen/samer/](https://benthic.io/ngopen/samer/)             |
| `irs_ng`      | `irs_ng`              | IRS BMF, Form 990, 527s           | [/ngopen/irs_ng/](https://benthic.io/ngopen/irs_ng/)           |
| `usp_cl`      | `us_project_cl`       | unitedstates/congress-legislators | [/ngopen/usp_cl/](https://benthic.io/ngopen/usp_cl/)           |
| `up_cdmaps`   | `ucla_polysci_cdmaps` | UCLA PolySci district boundaries  | [/ngopen/up_cdmaps/](https://benthic.io/ngopen/up_cdmaps/)     |

They are designed to be joined. Entities link across `usaspending` and `samer`
by UEI, reach `irs_ng` heuristically by DUNS≈EIN, and resolve to districts in
`up_cdmaps` and representatives in `usp_cl` spatially. The declared join paths
live in the collection manifest.

---

## Quick start

```bash
python3 -m venv .venv && ./.venv/bin/pip install -e .
export NGOPEN_CONFIG=$PWD/ngopen.toml

ngopen stages                  # the nine stages
ngopen run usp_cl              # smallest dataset — good first run
ngopen status usp_cl           # what completed, what didn't
```

See [MIGRATION.md](MIGRATION.md) for prerequisites, storage requirements, and
the from-scratch procedure for the larger datasets.

---

## Stages

Every dataset runs the same nine stages in the same order. A stage that does
not apply returns `skipped` rather than being omitted, so ledgers read
identically across datasets.

| Stage        | Does                                                        |
| ------------ | ----------------------------------------------------------- |
| `00_acquire` | Fetch from upstream. Resumable by byte offset.              |
| `01_verify`  | Validate the artifacts before touching the database.        |
| `02_restore` | Create the database, apply schema and keys, load base data. |
| `03_schema`  | Add geocoding columns.                                      |
| `04_index`   | Constraints, foreign keys, secondary indexes.               |
| `05_geocode` | Photon, resumable by row-id cursor.                         |
| `06_derive`  | Materialized views, views, RPCs.                            |
| `07_analyze` | `ANALYZE`.                                                  |
| `08_expose`  | Grant to the PostgREST roles.                               |

Indexes deliberately come after the bulk load — loading into an unindexed
table is substantially faster and the end state is identical.

```bash
ngopen run irs_ng --only 06_derive
ngopen run irs_ng --start-at 04_index
ngopen run irs_ng --only 05_geocode --force
ngopen run usaspending --variant subset --dbname usaspending_bdp_validate
```

---

## Configuration

One file: `ngopen.toml`. Paths, database names, roles, geocoder endpoints,
source URLs. No connection strings or filesystem paths appear anywhere else in
the codebase.

Resolution order:

1. `--config PATH`
2. `$NGOPEN_CONFIG`
3. `./ngopen.toml`
4. repository root
5. `~/.config/ngopen/ngopen.toml`

Secrets are never stored in it. See MIGRATION.md §4.

---

## Layout

```
ngopen.toml               central configuration
src/ngopen_bdp/           shared machinery
  config.py               TOML loader
  db.py                   psql / pg_restore / psycopg2
  fetch.py                resumable downloads
  geocode.py              the single Photon client
  ledger.py               bdp_meta.run_ledger, crash recovery
  log.py                  one logging setup
  stages.py               stage contract and runner
  cli.py                  ngopen
pipelines/<dataset>/
  pipeline.py             the nine stages
  sql/                    schema, keys, constraints, derived objects
recovered/<dataset>/      DDL recovered from live databases
MIGRATION.md              provenance audit and operational guide
```

### `recovered/`

Twelve objects serving live traffic — materialized views, spatial RPCs, and a
set of geocoding columns — existed only in the production catalogs, created by
hand and never committed anywhere. They were extracted from
`pg_get_viewdef` / `pg_get_functiondef` and are shipped here under provenance
headers, labelled `recovered` rather than `derived` in the manifests.

That distinction is the point of the exercise. See MIGRATION.md §3.

---

## Verifying a dataset

```bash
curl -s https://benthic.io/bdp/ngopen/usaspending/manifest.json > m.json
bdp verify m.json
```

The manifest names the repository and commit that produced the data, lists
every relation and column, and is signed with the publisher's Ed25519 key.
Protocol details: <https://benthic.io/bdp/>.

---

## License

MIT.
