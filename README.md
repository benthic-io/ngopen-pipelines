# ngopen-pipelines

ETL pipelines for the **NGOpen** collection — five public PostgREST APIs over
U.S. government spending, nonprofit, and legislative data, published at
<https://benthic.io/ngopen/>.

Every pipeline runs from scratch in the complete absence of data, refreshes in
place when re-run, and resumes where it left off after a crash. Each publishes
a signed [BDP](https://benthic.io/bdp/) manifest so anyone can verify that the
code in this repository produced the data being served.

---

## The collection

| Dataset       | Database              | Source                            | Endpoint                                                       | Pipeline                                  |
| ------------- | --------------------- | --------------------------------- | -------------------------------------------------------------- | ----------------------------------------- |
| `usaspending` | `usaspending_db`      | USAspending.gov bulk archive      | [/ngopen/usaspending/](https://benthic.io/ngopen/usaspending/) | [README](pipelines/usaspending/README.md) |
| `samer`       | `sam_er`              | SAM.gov entity registrations      | [/ngopen/samer/](https://benthic.io/ngopen/samer/)             | [README](pipelines/samer/README.md)       |
| `irs_ng`      | `irs_ng`              | IRS BMF, Form 990, 527s           | [/ngopen/irs_ng/](https://benthic.io/ngopen/irs_ng/)           | [README](pipelines/irs_ng/README.md)      |
| `usp_cl`      | `us_project_cl`       | unitedstates/congress-legislators | [/ngopen/usp_cl/](https://benthic.io/ngopen/usp_cl/)           | [README](pipelines/usp_cl/README.md)      |
| `up_cdmaps`   | `ucla_polysci_cdmaps` | UCLA PolySci district boundaries  | [/ngopen/up_cdmaps/](https://benthic.io/ngopen/up_cdmaps/)     | [README](pipelines/up_cdmaps/README.md)   |

They are designed to be joined. Entities link across `usaspending` and `samer`
by UEI, reach `irs_ng` heuristically by DUNS≈EIN, and resolve to districts in
`up_cdmaps` and representatives in `usp_cl` spatially. The declared join paths
live in the [signed collection manifest](https://benthic.io/bdp/ngopen/collection.json).

Each pipeline README documents what that dataset actually does — its source,
its relations, its recovered objects, and the things that will bite you. Start
there when you are working on one dataset rather than five.

---

## Quick start

```bash
python3 -m venv .venv && ./.venv/bin/pip install -e .
export NGOPEN_CONFIG=$PWD/ngopen.toml

ngopen stages                  # the nine stages
ngopen run usp_cl              # smallest dataset — good first run
ngopen status usp_cl           # what completed, what didn't
```

Start with `usp_cl` or `up_cdmaps`: both are a few gigabytes, both build in
minutes, and both are structurally clean apart from the six PostGIS catalog
grants described in their READMEs. `usaspending` needs ~2.5 TB and days.

See [AUDIT.md](AUDIT.md) §4 for prerequisites and the from-scratch procedure
for the larger datasets.

---

## The stage contract

Every dataset runs the same nine stages in the same order. A stage that does
not apply returns `skipped` rather than being omitted, so ledgers read
identically across datasets and an auditor can see at a glance that, say,
`samer` has no dump-restore step because its source is a flat file.

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

This table is the _contract_. What each dataset actually does inside each
stage differs substantially — `usaspending` has no `10_schema.sql` at all, and
`up_cdmaps` has no `25_derived_indexes.sql`. Read the per-pipeline README for
that.

Stages are idempotent. Re-running a completed pipeline performs a refresh, not
a rebuild: `00_acquire` re-checks the source for a newer artifact and
everything downstream reacts to whether it found one.

---

## Commands

| Command                    | Does                                                                       |
| -------------------------- | -------------------------------------------------------------------------- |
| `ngopen stages`            | List the canonical stage sequence.                                         |
| `ngopen config`            | Print the resolved configuration file path.                                |
| `ngopen run <dataset>`     | Run (or resume) a pipeline.                                                |
| `ngopen status <dataset>`  | Per-stage ledger state.                                                    |
| `ngopen reset <dataset>`   | Clear ledger rows so stages re-run.                                        |
| `ngopen compare <dataset>` | Diff two databases: structural (a gate) and content (advisory).            |
| `ngopen migrate <dataset>` | Move a live dataset onto pipeline-built relations, one relation at a time. |

`ngopen run` accepts `--only`, `--start-at`, `--force`, `--dry-run`, `--limit`,
`--variant`, and `--dbname`. `--dbname` is for validation runs and must never
point at a serving database.

```bash
ngopen run irs_ng --only 06_derive
ngopen run irs_ng --start-at 04_index
ngopen run irs_ng --only 05_geocode --force
ngopen run usaspending --variant subset --dbname usaspending_bdp_validate
```

`ngopen compare` and `ngopen migrate` are documented separately in
[MIGRATE.md](MIGRATE.md). They exist to move a running production database
onto relations built by this code without a maintenance window.

---

## Configuration

One file: `ngopen.toml`. Paths, database names, roles, geocoder endpoints,
source URLs. No connection strings or filesystem paths appear anywhere else in
the codebase.

Resolution order, first hit wins:

1. `--config PATH`
2. `$NGOPEN_CONFIG`
3. `./ngopen.toml`
4. the repository root
5. `~/.config/ngopen/ngopen.toml`

Secrets are never stored in it. The documented home is
`~/.config/ngopen/env`, mode `0600`, sourced by the systemd units. See
[AUDIT.md](AUDIT.md) §4.

---

## Layout

```text
ngopen.toml               central configuration
pipelines/<dataset>/
  pipeline.py             the nine stages for this dataset
  README.md               what this dataset actually does
  sql/                    schema, keys, constraints, derived objects
src/ngopen_bdp/           shared machinery
  __init__.py             stage contract re-exports
  config.py               TOML loader
  db.py                   psql / pg_restore / psycopg2
  fetch.py                resumable downloads
  geocode.py              the single Photon client
  ledger.py               bdp_meta.run_ledger, crash recovery
  log.py                  one logging setup
  stages.py               stage contract and runner
  cli.py                  ngopen
  compare.py              structural + content database diff
  migrate.py              relation-at-a-time live migration
recovered/<dataset>/      DDL recovered from live databases
audit/                    generated comparison and drift reports
HOUSE-STYLE.md            required document structure
check_docs.py             checks this repository against it
MIGRATE.md                live migration runbook
AUDIT.md                  provenance audit and operational guide
LICENSE
```

### `recovered/`

Twelve objects serving live traffic — materialized views, spatial RPCs, and a
set of geocoding columns — existed only in the production catalogs, created by
hand and never committed anywhere. They were extracted from
`pg_get_viewdef` / `pg_get_functiondef` and are shipped here under provenance
headers, labelled `recovered` rather than `derived` in the manifests.

That distinction is the point of the exercise. Two further hand-built objects
sit in the same directory and are not in that count of twelve: the
`geom_point_trigger` function and trigger, and three unexplained extensions.
See [AUDIT.md](AUDIT.md) §3 and
[`pipelines/usaspending/README.md`](pipelines/usaspending/README.md).

### `audit/`

Generated output from `ngopen compare`, kept in the repository because it is
the evidence for the provenance claims in [AUDIT.md](AUDIT.md). The
`structural-*.md` files are machine-generated and will be superseded; the
`*-resolution.md` and `*-raw-drop.md` files are written records and will not
be. Indexed in [MIGRATE.md](MIGRATE.md) §7.

---

## Verifying a dataset

```bash
curl -s https://benthic.io/bdp/ngopen/usaspending/manifest.json > m.json
bdp verify m.json
```

The manifest names the repository and commit that produced the data, lists
every relation and column, and is signed with the publisher's Ed25519 key.
Protocol details: <https://benthic.io/bdp/>.

To check the local build instead of the published one:

```bash
ngopen status usp_cl
ngopen compare usp_cl --right us_project_cl_bdp_next
```

`ngopen compare` exits non-zero on structural drift, so it can gate a script.

---

## Operations

Running a pipeline against a live host — comparing a candidate, swapping one
relation at a time, rolling back, reclaiming disk — is documented in
[MIGRATE.md](MIGRATE.md). Read it before running `ngopen migrate` against
anything serving traffic.

Provenance, storage requirements, refresh cadence, and crash recovery are in
[AUDIT.md](AUDIT.md).

---

## Documentation

| Document                                               | What it covers                                                       |
| ------------------------------------------------------ | -------------------------------------------------------------------- |
| [README.md](README.md)                                 | This file — the collection, the contract, the commands.              |
| [HOUSE-STYLE.md](HOUSE-STYLE.md)                       | Required structure for every document here.                          |
| [MIGRATE.md](MIGRATE.md)                               | `ngopen compare` and `ngopen migrate`: the live migration runbook.   |
| [AUDIT.md](AUDIT.md)                                   | Provenance history, recovered DDL, storage, cadence, crash recovery. |
| [`pipelines/<ds>/README.md`](pipelines/)               | Per-dataset source, relations, recovered objects, gotchas.           |
| [`audit/`](audit/)                                     | Generated comparison and drift reports.                              |
| [benthic.io/docs/](https://benthic.io/docs/)           | The public API reference.                                            |
| [benthic.io/apis/](https://benthic.io/apis/)           | Join paths, use cases, and cross-collection queries.                 |
| [BDP specification](https://github.com/benthic-io/bdp) | The manifest and signing protocol.                                   |

### Development

```bash
ruff check .
python3 check_docs.py            # documentation structure
```

`check_docs.py` takes no arguments. It exits 0 clean, 1 on a violation, and
prints every problem it found rather than stopping at the first.

---

## License

MIT. See [LICENSE](LICENSE).
