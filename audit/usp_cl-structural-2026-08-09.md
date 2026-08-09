# usp_cl

Generated 2026-08-09T15:46:35Z

| | |
|---|---|
| Reference (left) | `us_project_cl` |
| Candidate (right) | `us_project_cl_bdp_next` |
| Schemas | `public` |

## Structural comparison

Structural equivalence is a gate. Every difference below is either a defect in the candidate pipeline or a change made by hand in the reference database that was never written back to source.

**Verdict: FAIL**

| Aspect | Only in reference | Only in candidate | Changed |
|---|---:|---:|---:|
| relations | 0 | 0 | 0 |
| columns | 0 | 2 | 0 |
| indexes | 0 | 8 | 0 |
| constraints | 0 | 8 | 0 |
| functions | 0 | 0 | 0 |
| grants | 6 | 0 | 0 |
| geometry | 0 | 0 | 0 |

### columns

**Only in `us_project_cl_bdp_next`** (2)

- `public.district_offices.geocode_date`
- `public.district_offices.geocode_system`

### indexes

**Only in `us_project_cl_bdp_next`** (8)

- `public.committee_membership.committee_membership_natural_key`
- `public.committees.committees_natural_key`
- `public.district_offices.district_offices_natural_key`
- `public.executive_terms.executive_terms_natural_key`
- `public.legislator_other_names.legislator_other_names_natural_key`
- `public.legislator_social_media.legislator_social_media_natural_key`
- `public.legislator_terms.legislator_terms_natural_key`
- `public.subcommittees.subcommittees_natural_key`

### constraints

**Only in `us_project_cl_bdp_next`** (8)

- `public.committee_membership.committee_membership_natural_key`
- `public.committees.committees_natural_key`
- `public.district_offices.district_offices_natural_key`
- `public.executive_terms.executive_terms_natural_key`
- `public.legislator_other_names.legislator_other_names_natural_key`
- `public.legislator_social_media.legislator_social_media_natural_key`
- `public.legislator_terms.legislator_terms_natural_key`
- `public.subcommittees.subcommittees_natural_key`

### grants

**Only in `us_project_cl`** (6)

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
| `public.committee_membership` | unknown | 3,891 |  |  |
| `public.committees` | unknown | 76 |  |  |
| `public.district_offices` | 1,312 | 1,306 | -6 | -0.5% |
| `public.executive_terms` | unknown | 107 |  |  |
| `public.executives` | unknown | 67 |  |  |
| `public.legislator_other_names` | unknown | 5 |  |  |
| `public.legislator_social_media` | unknown | 518 |  |  |
| `public.legislator_terms` | unknown | 45,533 |  |  |
| `public.legislators` | unknown | 12,768 |  |  |
| `public.mv_committee_power` | unknown | 1,339 |  |  |
| `public.mv_current_lawmakers` | unknown | 537 |  |  |
| `public.subcommittees` | unknown | 200 |  |  |

