# up_cdmaps

Generated 2026-08-09T17:03:32Z

| | |
|---|---|
| Reference (left) | `ucla_polysci_cdmaps` |
| Candidate (right) | `ucla_polysci_cdmaps_bdp_next` |
| Schemas | `public` |

## Structural comparison

Structural equivalence is a gate. Every difference below is either a defect in the candidate pipeline or a change made by hand in the reference database that was never written back to source.

**Verdict: FAIL**

| Aspect | Only in reference | Only in candidate | Changed |
|---|---:|---:|---:|
| relations | 0 | 0 | 0 |
| columns | 0 | 0 | 0 |
| indexes | 0 | 0 | 0 |
| constraints | 0 | 0 | 0 |
| functions | 0 | 0 | 0 |
| grants | 6 | 0 | 0 |
| geometry | 0 | 0 | 0 |

### grants

**Only in `ucla_polysci_cdmaps`** (6)

- `public.geography_columns.api_user.SELECT`
- `public.geography_columns.web_anon.SELECT`
- `public.geometry_columns.api_user.SELECT`
- `public.geometry_columns.web_anon.SELECT`
- `public.spatial_ref_sys.api_user.SELECT`
- `public.spatial_ref_sys.web_anon.SELECT`

## Content comparison

Row counts are advisory, never a gate. The reference database was built against an older upstream vintage; the candidate pulls current data. Differences are expected and are recorded here as the honest delta rather than treated as regressions. Counts are `reltuples` estimates, reported as unknown where a relation has never been analysed.

| Relation | Reference | Candidate | Delta | Change |
|---|---:|---:|---:|---:|
| `public.congressional_districts` | unknown | 39,297 |  |  |

