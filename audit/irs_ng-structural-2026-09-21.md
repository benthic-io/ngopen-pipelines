# irs_ng

Generated 2026-09-21T19:14:08Z

| | |
|---|---|
| Reference (left) | `irs_ng` |
| Candidate (right) | `irs_ng_v4` |
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
| grants | 0 | 16 | 0 |
| geometry | 0 | 0 | 0 |

### grants

**Only in `irs_ng_v4`** (16)

- `public.bmf_organization_snapshots.api_user.SELECT`
- `public.bmf_organizations.api_user.SELECT`
- `public.census_demographics.api_user.SELECT`
- `public.form990_details.api_user.SELECT`
- `public.form990_schedule_o.api_user.SELECT`
- `public.form990_soi.api_user.SELECT`
- `public.form990_soi_private_foundation.api_user.SELECT`
- `public.form990_xml_import_log.api_user.SELECT`
- `public.form990n_small_orgs.api_user.SELECT`
- `public.form990t_details.api_user.SELECT`
- `public.political_orgs_527.api_user.SELECT`
- `public.pub78_eligible.api_user.SELECT`
- `public.revoked_organizations.api_user.SELECT`
- `public.v_org_financial_profile.api_user.SELECT`
- `public.v_org_multi_year.api_user.SELECT`
- `public.v_political_orgs.api_user.SELECT`

