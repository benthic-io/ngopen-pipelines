# Migration

How the legacy `ngopen` scripts became these pipelines, what was recovered
along the way, and what it costs to run any of this from scratch.

---

## 1. Migration status

Each dataset's BDP manifest carries `etl_provenance.migration_status`. It
starts at `pending` — pinned to the scaffold commit — and tightens to
`migrated` once that pipeline has been proven end to end against real data.

| Dataset       | Legacy script(s)                                    | Pipeline                 | Status  |
| ------------- | --------------------------------------------------- | ------------------------ | ------- |
| `usaspending` | `geocode_usas.py`, `build_entity_awards.py`         | `pipelines/usaspending/` | pending |
| `samer`       | `gov_to_pg.py`, `sam_pipeline.py`, `geocode_sam.py` | `pipelines/samer/`       | pending |
| `irs_ng`      | `irs_ng.py`                                         | `pipelines/irs_ng/`      | pending |
| `usp_cl`      | `us_project_to_pg.py`                               | `pipelines/usp_cl/`      | pending |
| `up_cdmaps`   | `ucla_cd_to_pg.py`                                  | `pipelines/up_cdmaps/`   | pending |

Advancing a row means re-signing that manifest. The git history of the
published manifests is therefore the migration audit trail.

---

## 2. What changed, and why

The legacy scripts worked. They were not auditable.

| Legacy                                                            | Now                                                       |
| ----------------------------------------------------------------- | --------------------------------------------------------- |
| 6 different `get_db_connection` idioms                            | one `ngopen_bdp.db`                                       |
| `password = "postgres"` hardcoded in 5 files                      | `ngopen.toml`, secrets via env only                       |
| 3 CLI flag conventions (`--host` / `--db-host` / `--sam-db-host`) | one `ngopen run <dataset>`                                |
| 5 logging approaches                                              | one `ngopen_bdp.log`                                      |
| 3 incompatible geocoders                                          | one `ngopen_bdp.geocode`                                  |
| f-string SQL, including interpolated _values_                     | parameterised throughout                                  |
| Photon LAN IPs in 4 files                                         | `[geocoder].endpoints`                                    |
| `us_project_to_pg.py` dropped its database every run              | never drops; every insert upserts                         |
| no resume; a crash meant starting over                            | `bdp_meta.run_ledger`, resume at the last completed stage |
| no record of what produced a given table                          | `recovered/` plus signed manifests                        |

### The SQL injection

`geocode_usas.write_results_batch` built its `INSERT ... VALUES` clause by
f-string concatenation of raw values. Any recipient name containing an
apostrophe was a syntax error at best. It is replaced by
`geocode.write_results`, which uses `execute_batch` with bound parameters and
validates table and column identifiers against a regex before interpolating
them.

---

## 3. Recovered DDL

Cross-referencing the live catalogs against every line of the legacy scripts
turned up **12 database objects that exist in production, are documented on
benthic.io, and have no source code anywhere.** They were created by hand in
`psql` and never written down.

| Database              | Object                                 | Kind              |
| --------------------- | -------------------------------------- | ----------------- |
| `usaspending_db`      | `mv_entity_spending_summary`           | materialized view |
| `usaspending_db`      | `mv_district_spending`                 | materialized view |
| `usaspending_db`      | `mv_covid_spending`                    | materialized view |
| `usaspending_db`      | `rpt.recipient_lookup` geocode columns | 4 columns         |
| `irs_ng`              | `mv_nonprofit_profile`                 | materialized view |
| `irs_ng`              | `mv_org_financial_health`              | materialized view |
| `irs_ng`              | `rpc_nonprofits_in_district`           | function          |
| `irs_ng`              | `rpc_nonprofits_nearby`                | function          |
| `us_project_cl`       | `mv_current_lawmakers`                 | materialized view |
| `us_project_cl`       | `mv_committee_power`                   | materialized view |
| `ucla_polysci_cdmaps` | `rpc_find_district`                    | function          |
| `ucla_polysci_cdmaps` | `rpc_districts_in_bbox`                | function          |

Each was extracted from `pg_get_viewdef` / `pg_get_functiondef` into
`recovered/<dataset>/`, under a header stating exactly where it came from and
why it has no upstream source. They are labelled `provenance: "recovered"` in
the manifests rather than `derived`, because calling a hand-built object
"derived" would misrepresent it.

Three extensions — `cube`, `earthdistance`, `fuzzystrmatch` — are installed in
`usaspending_db` but appear in neither the upstream dump's requirements nor any
script. Captured in `recovered/usaspending/extensions_recovered.sql`.

### Indexes

327 indexes across the five databases, attributed by reading the scripts:

| Database              | Coded  | Constraint-backed | Recovered | Total   |
| --------------------- | ------ | ----------------- | --------- | ------- |
| `usaspending_db`      | 35     | 2                 | 76        | 113     |
| `sam_er`              | 9      | 2                 | 16        | 27      |
| `irs_ng`              | 20     | 26                | 56        | 102     |
| `us_project_cl`       | 21     | 10                | 43        | 74      |
| `ucla_polysci_cdmaps` | 4      | 2                 | 5         | 11      |
| **Total**             | **89** | **42**            | **196**   | **327** |

_Coded_ means a `CREATE INDEX` with that name exists in a legacy script.
_Recovered_ means it exists only in the live catalog.

Note that the upstream USAspending archive ships **zero** indexes — all 113 on
`usaspending_db`, including the ten on the read-only `rpt` schema, are
benthic's.

Three redundant pairs are reproduced as-is for audit fidelity rather than
silently cleaned up:

- `idx_ae_uei` and `idx_all_entities_uei`
- `idx_geocode_geom_point` and `idx_rgi_geom_point`
- `idx_recipient_geocode_source`, `idx_rgi_source_id`, and `recipient_geocode_index_pkey`

Dropping them is a separate, reviewable change.

---

## 4. Running from scratch

Every pipeline assumes no data exists. It fetches, restores, indexes,
geocodes, derives, and exposes. Re-running fetches whatever the source has
published since and updates in place.

```bash
git clone https://github.com/benthic-io/ngopen-pipelines
cd ngopen-pipelines
python3 -m venv .venv && ./.venv/bin/pip install -e .

cp ngopen.toml /path/you/control/ngopen.toml   # edit [paths] at minimum
export NGOPEN_CONFIG=/path/you/control/ngopen.toml

./.venv/bin/ngopen run usp_cl        # ~40 MB, minutes — start here
./.venv/bin/ngopen run up_cdmaps     # ~2.8 GB
./.venv/bin/ngopen run samer         # ~1.6 GB
./.venv/bin/ngopen run irs_ng        # ~35 GB, hours
./.venv/bin/ngopen run usaspending   # ~164 GB archive, days
```

### Prerequisites

- PostgreSQL 15 or later with PostGIS (18.3 / 3.6 in production)
- A superuser role named `root` — the upstream USAspending archive's objects
  are owned by `root`, and creating the role is cleaner than restoring with
  `--no-owner` and losing the ownership record:
  ```sql
  CREATE ROLE root SUPERUSER LOGIN;
  ```
- A reachable Photon geocoder, listed in `[geocoder].endpoints`. Dead
  endpoints are dropped at stage start rather than stalling the run; if none
  survive, `05_geocode` fails loudly.
- `pg_restore`, `psql`, `unzip`. `aria2c` is optional but strongly
  recommended — it is used automatically for downloads over 256 MB.

### Secrets

Never in `ngopen.toml`. The documented home is `~/.config/ngopen/env`, mode
`0600`, sourced by the systemd units:

```sh
SAM_API_KEY=...      # optional
CENSUS_API_KEY=...   # optional
```

`SAM_API_KEY` is only needed if you want `samer`'s `00_acquire` to pull the
monthly extract automatically. Without it the stage fails with a message
naming the exact file to download from
`https://sam.gov/data-services/Entity%20Registration%20Data` and where to put
it. Get a key from your SAM.gov account under Account Details → Public API Key.

`CENSUS_API_KEY` is not required at all — the ACS5 endpoint serves
unauthenticated requests below roughly 500 per day per IP, which is enough for
`irs_ng`. A key at <https://api.census.gov/data/key_signup.html> raises that
ceiling.

---

## 5. Storage

All working data lives under `[paths].root`, which production sets to
`/raid_0/ngopen`. Nothing is written outside it.

| Dataset       | Archives                       | Restored database |
| ------------- | ------------------------------ | ----------------- |
| `usp_cl`      | ~11 MB                         | ~40 MB            |
| `up_cdmaps`   | ~2.8 GB                        | ~4.5 GB           |
| `samer`       | ~1.6 GB                        | ~6 GB             |
| `irs_ng`      | ~35 GB                         | ~40 GB            |
| `usaspending` | ~164 GB zip + ~130 GB expanded | **~1.1 TB**       |

### The USAspending problem

A full from-scratch USAspending run needs roughly **1.4 TB** transiently: the
164 GB archive, the ~130 GB expanded dump directory, and the ~1.1 TB restored
database. Because the existing `usaspending_db` cannot be dropped until its
replacement is proven, a true regeneration needs both resident at once —
call it 2.5 TB.

`/raid_0` is 3.7 TB with ~1.2 TB free. **A full regeneration is not possible
in place today.** Before attempting one, reclaim from:

- `/raid_0/qtor` — 520 GB
- `/raid_0/osm_planet` — 426 GB
- `/raid_0/planetiler-tmp` — 91 GB

Or stage onto `/datastore_1` (1.9 TB free) by pointing `[paths].work` there.

Use `--variant subset` for anything short of a real regeneration. The subset
archive is 4.6 GB and restores in hours instead of days.

---

## 6. Refresh cadence

Re-running a pipeline is the refresh. Stages that already completed are
skipped unless `--force`, so a rerun does the minimum: check the source, fetch
what is new, load it, refresh the derived objects.

| Dataset       | Source cadence             | Suggested schedule        |
| ------------- | -------------------------- | ------------------------- |
| `usaspending` | monthly archive            | monthly, `--variant full` |
| `samer`       | monthly extract            | monthly                   |
| `irs_ng`      | continuous, varies by feed | monthly                   |
| `usp_cl`      | continuous (git)           | weekly                    |
| `up_cdmaps`   | static historical          | never; run once           |

There is no scheduling in this repo by design. A systemd user timer is the
obvious host-side answer:

```ini
# ~/.config/systemd/user/ngopen@.service
[Service]
Type=oneshot
EnvironmentFile=%h/.config/ngopen/env
Environment=NGOPEN_CONFIG=%h/.config/ngopen/ngopen.toml
ExecStart=%h/benthic-io/projects/ngopen-pipelines/.venv/bin/ngopen run %i
```

---

## 7. Crash recovery

Each target database carries its own ledger at `bdp_meta.run_ledger`, so the
record of how a database was built lives inside it and travels with any dump.

```bash
ngopen status usaspending    # per-stage last known state
ngopen run usaspending       # resumes at the first stage not completed
```

On startup a run marks any stage still flagged `running` as `failed` — those
are orphans from a killed process — and warns. Long stages carry their own
internal resume state so a crash mid-stage does not discard the work:

- `00_acquire` resumes partial downloads by byte offset
- `02_restore` is driven by a `pg_restore --use-list` manifest
- `05_geocode` persists a row-id high-water mark per table
- ingest stages hash each input file and skip ones already loaded

To redo a stage deliberately:

```bash
ngopen run samer --only 05_geocode --force
ngopen reset samer --stage 05_geocode
```

---

## 8. Validation

`usaspending_bdp_validate` is a throwaway database built from the 4.6 GB
subset archive and exercised through all nine stages — real restore, real
geocoding, real materialized views. It never touches the five serving
databases.

```bash
ngopen run usaspending --variant subset --dbname usaspending_bdp_validate
```

It is retained as a regression fixture. Drop it once the migration is
complete and the full pipeline has been run in anger.
