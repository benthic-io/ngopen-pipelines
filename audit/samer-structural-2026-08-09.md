# samer

Generated 2026-08-09T19:10:43Z

| | |
|---|---|
| Reference (left) | `sam_er` |
| Candidate (right) | `sam_er_bdp_next` |
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
| grants | 0 | 1 | 0 |
| geometry | 0 | 0 | 0 |

### grants

**Only in `sam_er_bdp_next`** (1)

- `public.sam_registrations.api_user.SELECT`

## Content comparison

Row counts are advisory, never a gate. The reference database was built against an older upstream vintage; the candidate pulls current data. Differences are expected and are recorded here as the honest delta rather than treated as regressions. Counts are `reltuples` estimates, reported as unknown where a relation has never been analysed.

| Relation | Reference | Candidate | Delta | Change |
|---|---:|---:|---:|---:|
| `public.mv_contractor_registry` | unknown | 866,796 |  |  |
| `public.sam_registrations` | 856,290 | 2,597,460 | +1,741,170 | +203.3% |

