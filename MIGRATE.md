# MIGRATE

Moving a live production database onto relations built by this repository, one
relation at a time, without a maintenance window.

This is the runbook for `ngopen compare` and `ngopen migrate`. It is the
operational half of the work; [AUDIT.md](AUDIT.md) is the provenance half.

---

## The problem this solves

The five serving databases were built by hand and by six legacy scripts over
several years. They work, and they serve traffic, but nothing in the source
tree provably produced them. Auditing that turned up **twelve database objects
that exist in production, are documented on benthic.io, and have no source
code anywhere** — see [AUDIT.md](AUDIT.md) §3.

The obvious fix is to rebuild each database from scratch and swap it in. That
does not work here:

- `usaspending_db` is ~1.1 TB. Rebuilding it needs ~2.5 TB transiently and
  days of wall clock, during which the existing database must stay live.
- A full `DROP DATABASE` + restore is a maintenance window measured in days.
- Even where it is feasible, a cutover that replaces 1.1 TB of relations in one
  transaction is a single point of failure with no way back.

`ngopen migrate` inverts the unit of work. Instead of migrating a _database_,
it migrates a _relation_.

---

## How it works

The unit of migration is a **relation**, not a row range. That choice is forced
by Postgres:

- `DELETE` marks rows dead but returns nothing to the filesystem. Reclaiming
  the space needs `VACUUM FULL`, which transiently wants a second copy of the
  table.
- `DROP TABLE` returns the space immediately.

A migration meant to free disk as it proceeds has to move whole relations.

Serving continues throughout, because the cutover is a rename inside a single
transaction:

```sql
BEGIN;
  ALTER ... public.all_entities RENAME TO all_entities__bdp_legacy;
  ALTER ... bdp_next.all_entities SET SCHEMA public;
COMMIT;
```

PostgREST resolves relations per query, so in-flight statements finish against
the old relation and the next one lands on the new. No restart, no dropped
connection, no nginx change.

Two schemas carry the process:

| Name       | Role                                                        |
| ---------- | ----------------------------------------------------------- |
| `bdp_next` | Staging. Pipeline-built candidate relations are built here. |
| `bdp_meta` | Bookkeeping. `migration_state` and `run_ledger` live here.  |

Legacy copies keep the `__bdp_legacy` suffix.

### Relation states

Every relation carries a state in `bdp_meta.migration_state`, and the process
is stoppable at any of them:

| State       | Meaning                                      |
| ----------- | -------------------------------------------- |
| `legacy`    | Untouched, serving from the original.        |
| `building`  | Candidate copy present in `bdp_next`.        |
| `verified`  | Candidate passed structural comparison.      |
| `swapped`   | Serving from the candidate, legacy retained. |
| `reclaimed` | Legacy dropped, space returned.              |

**Rollback is available until reclaim.** That is the property that makes this
acceptable to run against a live host: from `legacy` through `swapped`, a
relation can be put back exactly as it was, at the cost of some disk.

### Comparison is a gate; row counts are not

`ngopen compare` produces two sections that answer different questions, and
conflating them would make the tool useless.

**Structural comparison is a gate.** Relations, columns, types, nullability,
indexes, constraints, functions and grants must match exactly. Every
difference is either a defect in the new pipeline or an undocumented change
made by hand in production that was never written back to the ETL source. Both
are findings worth acting on; neither is acceptable to wave through. A
non-zero exit lets callers script on it.

**Content comparison is advisory.** The live databases are stale — built
against older upstream vintages. A freshly built database pulls current data,
so row counts _will_ differ, and differing is the correct outcome. This section
records the honest delta so the report says what changed and by how much,
without pretending a growing dataset is a regression.

That distinction is why the `samer` candidate shows +203% rows with **zero**
structural differences, and why the `up_cdmaps` report is clean while `samer`'s
verdict is FAIL.

---

## Commands

### `ngopen compare`

```bash
ngopen compare <dataset> --right <candidate> [options]
```

| Option            | Does                                                       |
| ----------------- | ---------------------------------------------------------- |
| `--left <db>`     | Reference. Default: the serving database for this dataset. |
| `--right <db>`    | **Required.** The candidate.                               |
| `--schema <name>` | Schema to compare. Repeatable. Default `public`.           |
| `--no-content`    | Skip the advisory row-count section.                       |
| `--out <path>`    | Write the report to a file.                                |
| `--json`          | Emit JSON instead of markdown.                             |

Exit 0 if structurally clean, 1 if not.

### `ngopen migrate`

```bash
ngopen migrate <dataset> [options]
```

| Option              | Does                                                                               |
| ------------------- | ---------------------------------------------------------------------------------- |
| `--plan`            | Show the state of every relation. Implied when no `--relation` is given.           |
| `--candidate <db>`  | **Required** with `--relation`. The database holding pipeline-built relations.     |
| `--serving <db>`    | Serving database. Default: the dataset's configured database.                      |
| `--relation <name>` | Migrate this relation. Repeatable.                                                 |
| `--verify-only`     | Stage and compare, but do not cut over.                                            |
| `--force`           | Swap even if structural comparison failed, or reclaim a relation not in `swapped`. |
| `--rollback <name>` | Return this relation to its legacy copy.                                           |
| `--reclaim`         | Drop retained legacy relations. Irreversible.                                      |
| `--out <path>`      | Write the plan or comparison report.                                               |

---

## The procedure

**Step 1 — build the candidate.** Run the pipeline into an isolated database.
Never point this at a serving database:

```bash
ngopen run usp_cl --dbname us_project_cl_bdp_next
```

**Step 2 — compare, and read the report before you act on it.**

```bash
ngopen compare usp_cl --right us_project_cl_bdp_next --out /tmp/usp_cl.md
```

A `FAIL` here is information, not an obstacle. Classify each difference as a
pipeline defect, an undocumented production object, or an upstream vintage
change, and record the classification. That record is what
[`audit/usaspending-drift-resolution.md`](audit/usaspending-drift-resolution.md)
is; it is the model to follow.

The most common finding across the collection is six PostGIS catalog grants —
`geography_columns`, `geometry_columns`, `spatial_ref_sys` to `api_user` and
`web_anon` — that exist in serving databases and not in a fresh `postgis`
install. `usp_cl` and `up_cdmaps` differ by nothing else.

**Step 3 — plan.**

```bash
ngopen migrate usp_cl --plan
```

**Step 4 — stage and verify, without cutting over.**

```bash
ngopen migrate usp_cl \
  --candidate us_project_cl_bdp_next \
  --relation district_offices \
  --verify-only
```

**Step 5 — swap.**

```bash
ngopen migrate usp_cl \
  --candidate us_project_cl_bdp_next \
  --relation district_offices
```

Comparison runs once and gates the whole batch. A structural defect anywhere in
the candidate is a reason to stop, not a reason to migrate the parts that happen
to look fine.

### Relations that must move together

A relation joined to others by a foreign key cannot cut over alone, so asking
for one member of a cluster pulls in the rest. The CLI expands your
`--relation` list and prints what it added:

```text
foreign keys require these to move together, adding: legislators, legislator_terms
```

This is deliberate. A partial swap is not something you can ask for by
accident. A relation with no foreign keys can carry its constraints in during
staging; one inside a cluster cannot, because its references point at relations
still serving old data, so validation waits for the swap.

Swapping happens cluster by cluster, in one transaction per cluster. Unrelated
relations are independent, and a failure in one does not abandon the others.

---

## Rollback and reclaim

### Rollback

Available from any state up to and including `swapped`:

```bash
ngopen migrate usp_cl --rollback district_offices
```

Reverses the rename, restores serving from `__bdp_legacy`, and drops the
candidate copy from `bdp_next`. The relation is exactly as it was.

### Reclaim

Once a relation has been serving from its candidate long enough to be
confident, the legacy copy is dead weight:

```bash
ngopen migrate usp_cl --reclaim
```

**Irreversible.** There is nothing to roll back to afterwards. Reclaim is
separate from swap on purpose so that the window between "cut over" and "lose
the ability to go back" is a decision rather than a side effect.

Reclaim is also how the collection pays for itself: the `usaspending` migration
reclaimed 9/9 of the disk that held the duplicate copies, which is what made a
subsequent full rebuild possible at all.

---

## Audit reports

`audit/` holds the output of `ngopen compare` over time, kept because it is the
evidence for the provenance claims in [AUDIT.md](AUDIT.md).

**Machine-generated — superseded by later runs:**

| File                                                                                 | Reference → candidate                                  | Date       |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------ | ---------- |
| [`usp_cl-structural-2026-08-09.md`](audit/usp_cl-structural-2026-08-09.md)           | `us_project_cl` → `us_project_cl_bdp_next`             | 2026-08-09 |
| [`up_cdmaps-structural-2026-08-09.md`](audit/up_cdmaps-structural-2026-08-09.md)     | `ucla_polysci_cdmaps` → `ucla_polysci_cdmaps_bdp_next` | 2026-08-09 |
| [`samer-structural-2026-08-09.md`](audit/samer-structural-2026-08-09.md)             | `sam_er` → `sam_er_bdp_next`                           | 2026-08-09 |
| [`usaspending-structural-2026-08-09.md`](audit/usaspending-structural-2026-08-09.md) | `usaspending_db` → `usaspending_bdp_validate`          | 2026-08-09 |
| [`irs_ng-structural-2026-09-21.md`](audit/irs_ng-structural-2026-09-21.md)           | `irs_ng` → `irs_ng_v4`                                 | 2026-09-21 |
| [`usaspending-structural-2026-09-21.md`](audit/usaspending-structural-2026-09-21.md) | `usaspending_db` → `usaspending_bdp_next`              | 2026-09-21 |

**Written records — permanent, do not regenerate:**

| File                                                                       | What it is                                                                               |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| [`usaspending-drift-resolution.md`](audit/usaspending-drift-resolution.md) | Seven drift classes, each classified and resolved. The model for this kind of document.  |
| [`usaspending-raw-drop.md`](audit/usaspending-raw-drop.md)                 | Structural record of the dropped `raw.*` relations, kept so the removal stays auditable. |

To regenerate a report, rerun `ngopen compare` and write to the same path.

---

## Safety rules

What this subsystem will refuse to do, and what you must not do.

- **`--dbname` on `ngopen run` is for validation databases.** Pointing a
  validation run at a serving database risks destroying it. `ngopen migrate`
  additionally refuses to treat the configured serving database as a
  replacement target.
- **A relation inside a foreign-key cluster cannot be swapped alone.** The CLI
  expands the list. Do not work around this by swapping members in separate
  invocations; the second swap will fail on constraint validation against a
  relation that has already moved.
- **`--reclaim` is irreversible.** Do not reclaim in the same breath as the
  swap. Leave the legacy copy in place until the new one has served real
  traffic.
- **`--force` on a swap means a known-wrong candidate went live.** It exists
  for the case where the structural difference has been classified and
  accepted in writing, not for making a `FAIL` go away.
- **A full `usaspending` regeneration is not currently possible in place.** It
  needs ~2.5 TB and `/raid_0` has ~1.2 TB free. Reclaim from `/raid_0/qtor`
  (520 GB), `/raid_0/osm_planet` (426 GB), or `/raid_0/planetiler-tmp` (91 GB)
  first, or stage onto `/datastore_1` by pointing `[paths].work` there. See
  [AUDIT.md](AUDIT.md) §5.
- **A comparison report is not a result.** `performance-diagnosis`-style plans
  that read like findings are a known failure mode in this organisation. A
  `*-structural-*.md` file with a `**Verdict:**` line is a measurement; a
  `-resolution.md` file is a decision; neither is a summary. Read both halves
  of the record.
