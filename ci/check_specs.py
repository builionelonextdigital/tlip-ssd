#!/usr/bin/env python3
"""SDD gate: every commit tagged with a work-item code must have an approved spec.

Usage:
    python3 ci/check_specs.py                       # range from GitLab MR env, else origin/main...HEAD
    python3 ci/check_specs.py --range main...HEAD
    python3 ci/check_specs.py --message "[O2C No. 14] Add field"   # check one message (local/testing)
    python3 ci/check_specs.py --strict-ids          # also fail commits without any code

No third-party dependencies (reads the flat sdd.config.yml format itself).
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULTS = {
    "specs_dir": "specs",
    "id_regex": r"^\[(?P<prefix>[A-Z][A-Z0-9]+)(?: No\.)? ?#?(?P<num>\d+)\]",
    "exempt_prefixes": ["HOTFIX", "AUDIT", "CHORE"],
    "allowed_statuses": ["Approved", "Implementing", "Done"],
}
SKIP_SUBJECT = re.compile(r"^(Merge |Revert \")")


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [v.strip().strip("'\"") for v in raw[1:-1].split(",") if v.strip()]
    return raw.strip("'\"")


def load_config(root):
    cfg = dict(DEFAULTS)
    path = root / "sdd.config.yml"
    if not path.exists():
        print(f"[sdd] warning: {path} not found, using defaults")
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        if key.strip() in DEFAULTS:
            cfg[key.strip()] = parse_value(val)
    return cfg


def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    data = {}
    if not m:
        return data
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = re.split(r"\s+#\s", " " + val, maxsplit=1)[0]  # drop inline "# comment"
        data[key.strip()] = val.strip().strip("'\"")
    return data


SPEC_ONLY_PREFIXES = ("specs/", "docs/")


def commit_subjects(rng):
    """(sha, subject) for each non-merge commit; commits touching only specs/ or docs/ are dropped
    (spec and plan PRs are how a spec gets approved, so they cannot require an approved spec)."""
    out = subprocess.run(
        ["git", "log", "--no-merges", "--format=%h%x09%s", rng],
        check=True, capture_output=True, text=True,
    ).stdout
    result = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        files = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            check=True, capture_output=True, text=True,
        ).stdout.split()
        if files and all(f.startswith(SPEC_ONLY_PREFIXES) for f in files):
            continue
        result.append((sha, subject))
    return result


def default_range():
    base = os.environ.get("CI_MERGE_REQUEST_DIFF_BASE_SHA")
    if base:
        return f"{base}..HEAD"
    target = os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME") or os.environ.get("CI_DEFAULT_BRANCH") or "main"
    return f"origin/{target}...HEAD"


def check(subjects, cfg, root, strict_ids):
    id_re = re.compile(cfg["id_regex"])
    specs_dir = root / cfg["specs_dir"]
    errors, warnings, seen = [], [], {}
    for sha, subject in subjects:
        if SKIP_SUBJECT.match(subject):
            continue
        m = id_re.match(subject)
        if not m:
            (errors if strict_ids else warnings).append(f"{sha} no work-item code: {subject!r}")
            continue
        prefix, num = m.group("prefix"), m.group("num")
        if prefix in cfg["exempt_prefixes"]:
            continue
        item = f"{prefix}-{num}"
        if item in seen:
            continue
        seen[item] = sha
        spec = specs_dir / item / "spec.md"
        if not spec.exists():
            errors.append(f"{sha} {item}: missing {spec.relative_to(root)} (run /sdd-spec)")
            continue
        fm = read_frontmatter(spec)
        status = fm.get("status", "")
        if status not in cfg["allowed_statuses"]:
            errors.append(f"{sha} {item}: spec status is {status or 'empty'!r}, need one of {cfg['allowed_statuses']}")
        for who in ("business_approver", "technical_approver"):
            if not fm.get(who):
                errors.append(f"{sha} {item}: spec has no {who}")
        plan = spec.with_name("plan.md")
        if not plan.exists():
            errors.append(f"{sha} {item}: missing plan.md (run /sdd-plan)")
        elif read_frontmatter(plan).get("status") != "Approved":
            errors.append(f"{sha} {item}: plan.md is not Approved")
        tasks = spec.with_name("tasks.md")
        if tasks.exists():
            open_tasks = re.findall(r"^\s*- \[[ ~]\]", tasks.read_text(encoding="utf-8"), re.M)
            if open_tasks:
                warnings.append(f"{item}: {len(open_tasks)} task(s) not done in tasks.md")
        else:
            warnings.append(f"{item}: no tasks.md")
    return errors, warnings, seen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--range", help="git revision range, e.g. main...HEAD")
    ap.add_argument("--message", action="append", help="check a commit message instead of git log")
    ap.add_argument("--root", default=".", help="repo root (default: .)")
    ap.add_argument("--strict-ids", action="store_true", help="fail commits without a work-item code")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg = load_config(root)
    if args.message:
        subjects = [("msg", m) for m in args.message]
    else:
        rng = args.range or default_range()
        try:
            subjects = commit_subjects(rng)
        except subprocess.CalledProcessError as e:
            print(f"[sdd] cannot read git log for {rng}: {e.stderr.strip()}")
            return 2
        print(f"[sdd] checking {len(subjects)} commit(s) in {rng}")

    errors, warnings, seen = check(subjects, cfg, root, args.strict_ids)
    for w in warnings:
        print(f"[sdd] WARN  {w}")
    for e in errors:
        print(f"[sdd] ERROR {e}")
    print(f"[sdd] items: {', '.join(seen) or 'none'} | errors: {len(errors)} | warnings: {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
