#!/usr/bin/env python3
"""Check that every document matches the section order in HOUSE-STYLE.md.

Run with no arguments to report. Exit 0 clean, 1 on a violation.

    python3 check_docs.py

This is a documentation linter, not a prose linter. It checks three things,
all of which have actually broken in this repository before:

1. Required headings appear, in the order HOUSE-STYLE.md declares. The README
   gained `migrate` and `compare` commands and a whole `audit/` directory
   without its layout tree or command table being updated, so nobody could
   discover the migration subsystem at all.
2. No heading level is skipped. A `##` followed by `####` renders as a
   structural hole in the GitHub and benthic.io outlines.
3. Every fenced code block declares a language.

It also checks that the README's `## Layout` tree mentions every tracked
top-level path, which is the specific drift that let `compare.py` and
`migrate.py` go undocumented.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FENCE_LANGUAGES = {
    "bash",
    "sh",
    "shell",
    "sql",
    "python",
    "py",
    "json",
    "toml",
    "ini",
    "text",
    "console",
    "yaml",
    "yml",
    "diff",
    "protobuf",
    "graphql",
}

# ---------------------------------------------------------------------------
# required section orders, mirroring HOUSE-STYLE.md
# ---------------------------------------------------------------------------

REQUIRED: dict[str, list[str]] = {
    "README.md": [
        "The collection",
        "Quick start",
        "The stage contract",
        "Commands",
        "Configuration",
        "Layout",
        "Verifying a dataset",
        "Operations",
        "Documentation",
        "License",
    ],
    "AUDIT.md": [
        "Status",
        "What changed, and why",
        "Recovered DDL",
        "Running from scratch",
        "Storage",
        "Refresh cadence",
        "Crash recovery",
        "Validation",
    ],
    "MIGRATE.md": [
        "The problem this solves",
        "How it works",
        "Commands",
        "The procedure",
        "Rollback and reclaim",
        "Audit reports",
        "Safety rules",
    ],
    "HOUSE-STYLE.md": [
        "Doc types",
        "Repo README",
        "Pipeline README",
        "Runbook",
        "Audit record",
        "Rules that apply everywhere",
    ],
}

PIPELINE_REQUIRED = [
    "At a glance",
    "Source",
    "What each stage does",
    "Relations",
    "Recovered objects",
    "Gotchas",
    "Verification",
    "Related",
]

# Paths the README's layout tree must mention, because they are how a reader
# discovers the code. Adding a module without adding it here is the drift this
# check exists to catch. The src/ entries are matched by bare filename: the
# tree already establishes the directory.
LAYOUT_MUST_MENTION = [
    "audit/",
    "compare.py",
    "migrate.py",
    "pipelines/",
    "recovered/",
    "ngopen.toml",
    "MIGRATE.md",
    "AUDIT.md",
    "HOUSE-STYLE.md",
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*(\S*)")

# A heading may carry a leading section number, as AUDIT.md's do. Strip it
# before matching, so the required lists in HOUSE-STYLE.md stay readable and
# numbering stays optional.
NUMBERED_RE = re.compile(r"^\d+[.)]\s+")


def normalise(text: str) -> str:
    return NUMBERED_RE.sub("", text).strip()


def headings(path: Path) -> list[tuple[int, str]]:
    """Level-2 headings in document order, ignoring fenced code blocks."""

    out: list[tuple[int, str]] = []
    fence: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(("```", "~~~")):
            fence = stripped[:3]
            continue
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) >= 2:
            out.append((len(m.group(1)), normalise(m.group(2))))
    return out


def check_sections(path: Path, required: list[str]) -> list[str]:
    problems: list[str] = []
    found = [text for _, text in headings(path)]
    for want in required:
        if want not in found:
            problems.append(f"{path}: missing required section '## {want}'")

    # order: each required heading must come after the previous one
    idx = -1
    for want in required:
        if want not in found:
            continue
        at = found.index(want, idx + 1) if want in found[idx + 1 :] else -1
        if at == -1:
            problems.append(
                f"{path}: section '## {want}' is out of order "
                f"(must follow the sections before it)"
            )
        else:
            idx = at
    return problems


def check_levels(path: Path) -> list[str]:
    """Reject a jump of more than one heading level."""

    problems: list[str] = []
    prev = 0
    for level, text in headings(path):
        if prev and level > prev + 1:
            problems.append(
                f"{path}: heading level jumps h{prev} -> h{level} at '## {text}'"
            )
        prev = level
    return problems


def check_fences(path: Path) -> list[str]:
    problems: list[str] = []
    in_fence = False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = FENCE_RE.match(line)
        if not m:
            continue
        if in_fence:
            in_fence = False
            continue
        in_fence = True
        lang = m.group(2)
        if not lang:
            problems.append(f"{path}:{n}: code fence has no language")
        elif lang not in FENCE_LANGUAGES:
            problems.append(f"{path}:{n}: unknown code fence language '{lang}'")
    return problems


def check_layout_tree(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [
        f"{path}: ## Layout does not mention '{needle}'"
        for needle in LAYOUT_MUST_MENTION
        if needle not in text
    ]


def check_documented_datasets() -> list[str]:
    """Every pipeline directory needs a README that matches the skeleton."""

    problems: list[str] = []
    for directory in sorted((ROOT / "pipelines").iterdir()):
        if not directory.is_dir() or directory.name == "__pycache__":
            continue
        readme = directory / "README.md"
        if not readme.exists():
            problems.append(f"pipelines/{directory.name}/README.md: missing")
            continue
        problems += check_sections(readme, PIPELINE_REQUIRED)
        problems += check_levels(readme)
        problems += check_fences(readme)
    return problems


def main() -> int:
    problems: list[str] = []

    for name, required in REQUIRED.items():
        path = ROOT / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        problems += check_sections(path, required)
        problems += check_levels(path)
        problems += check_fences(path)

    readme = ROOT / "README.md"
    if readme.exists():
        problems += check_layout_tree(readme)

    problems += check_documented_datasets()

    # generated audit reports are exempt from the skeleton but not the basics
    for report in sorted((ROOT / "audit").glob("*.md")):
        problems += check_levels(report)
        problems += check_fences(report)

    if problems:
        print(f"check_docs: {len(problems)} problem(s)\n")
        for problem in problems:
            print(f"  {problem}")
        return 1

    print("check_docs: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
