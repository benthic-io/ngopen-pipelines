# House style

The canonical section order for every document in this repository, and for the
other [benthic.io](https://benthic.io/) repositories.

The full rationale for this file lives at
[benthic-site/docs/STYLE.md](https://github.com/benthic-io/benthic-site/blob/main/docs/STYLE.md).
This copy is the short, enforceable list. `check_docs.py` reads the tables below
and fails the build when a document drifts from them, so if you change a
section order here, change it in `check_docs.py` in the same commit.

Run the check with:

```bash
python3 check_docs.py
```

## Doc types

Every document in this repository is exactly one of these types. Pick the type
first; the section order follows.

| Type             | Lives at                        | Has front matter |
| ---------------- | ------------------------------- | ---------------- |
| Repo README      | `README.md`                     | no               |
| Pipeline README  | `pipelines/<dataset>/README.md` | no               |
| Runbook          | `MIGRATE.md`                    | no               |
| Audit record     | `AUDIT.md`                      | no               |
| Style guide      | `HOUSE-STYLE.md`                | no               |
| Generated report | `audit/*.md`                    | no               |

## Repo README

Required headings, in order:

1. `# <repo name>`
2. `## The collection` — what this repo produces, and the dataset table
3. `## Quick start` — the shortest path to a working run
4. `## The stage contract` — what the nine stages are
5. `## Commands` — every CLI subcommand, one row each
6. `## Configuration` — the config file, resolution order, secrets
7. `## Layout` — the tree, complete
8. `## Verifying a dataset` — the BDP check
9. `## Operations` — pointer to the runbook
10. `## Documentation` — index of every other doc
11. `## License`

## Pipeline README

One per dataset in `pipelines/`. Required headings, in order:

1. `# <dataset> — <one line>`
2. `## At a glance` — the metadata table
3. `## Source` — what is fetched and from where
4. `## What each stage does` — the real bodies, not the generic contract
5. `## Relations` — tables, views, RPCs created and exposed
6. `## Recovered objects` — hand-built objects this pipeline must recreate
7. `## Gotchas` — the things that will bite you
8. `## Verification` — how to check a build
9. `## Related` — links out

`## What each stage does` is the section that justifies this document existing.
The repo README describes the contract; the pipeline README describes what this
dataset actually does. A reader debugging `05_geocode` on `samer` needs the
second, not the first.

## Runbook

1. `# <title>`
2. `## The problem this solves`
3. `## How it works` — the mechanism, including the parts that are surprising
4. `## Commands`
5. `## The procedure` — ordered steps
6. `## Rollback and reclaim`
7. `## Audit reports`
8. `## Safety rules` — what this will refuse to do

## Audit record

1. `# <title>`
2. `## Status` — current state, per dataset
3. `## What changed, and why`
4. `## Recovered DDL`
5. `## Running from scratch`
6. `## Storage`
7. `## Refresh cadence`
8. `## Crash recovery`
9. `## Validation`

## Rules that apply everywhere

- **Heading levels do not skip.** No `#` followed by `###`. The title is `#`,
  sections are `##`, subsections are `###`.
- **Every `##` heading is a noun phrase or a sentence**, never "Overview",
  "Introduction", "Misc", or "Other". `## Gotchas` is acceptable; `## Other` is
  not.
- **Tables before prose.** If a relationship fits in a table, it is a table.
- **Code fences carry a language.** Every fence is ` ```bash `,
  ` ```sql `, ` ```python `, ` ```json `, ` ```toml `,
  or ` ```ini `. A bare fence is a lint failure.
- **Absolute URLs for anything served.** `https://benthic.io/ngopen/...`, not
  `../` or a bare path, because these documents are read on GitHub as often as
  in a checkout.
- **State facts with a date and a source.** "As of 2026-09-21" plus a link to
  the manifest beats an undated assertion. Anything derived from a published
  manifest should say so.
- **No `## Overview`.** The title and the first paragraph are the overview.
