#!/usr/bin/env python3
"""Sync SDD spec/plan status into GitHub Issues (labels) and, optionally, a Projects v2 board.

Each Issue titled "[O2C No. 14] ..." maps to specs/O2C-14/. The stage is derived from
spec.md / plan.md front matter and written as one `status:*` label (+ `ai:*`, `shared-module`).

Env:
  GITHUB_TOKEN, GITHUB_REPOSITORY        required (except --dry-run with --issues-json)
  PROJECT_TOKEN, PROJECT_OWNER, PROJECT_NUMBER   optional: also set the board's "Status" field
  SDD_ALLOW_BACKWARD=1                    allow moving back to Spec Draft / Spec Review (change request on main)

Usage:
  python3 ci/sdd_sync.py [--dry-run] [--issues-json file]
No third-party dependencies.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_specs import load_config, read_frontmatter  # noqa: E402

# (label, board option name) in workflow order
STAGES = [
    ("status:backlog", "Backlog"),
    ("status:spec-draft", "Spec Draft"),
    ("status:spec-review", "Spec Review"),
    ("status:spec-approved", "Spec Approved"),
    ("status:plan-review", "Plan Review"),
    ("status:ready-to-build", "Ready to build"),
    ("status:implementing", "Implementing"),
    ("status:done", "Done"),
    ("status:dropped", "Dropped"),
]
RANK = {label: i for i, (label, _) in enumerate(STAGES)}
BOARD = dict(STAGES)
AI_LABELS = {"cao": "ai:cao", "trung bình": "ai:trung-binh", "trung binh": "ai:trung-binh", "thấp": "ai:thap", "thap": "ai:thap"}
API = "https://api.github.com"


def stage_of(spec_dir):
    spec = read_frontmatter(spec_dir / "spec.md")
    s = spec.get("status", "")
    plan_path = spec_dir / "plan.md"
    plan = read_frontmatter(plan_path) if plan_path.exists() else {}
    if s == "Dropped":
        return "status:dropped"
    if s == "Done":
        return "status:done"
    if s == "Implementing":
        return "status:implementing"
    if s == "Approved":
        if not plan:
            return "status:spec-approved"
        return "status:ready-to-build" if plan.get("status") == "Approved" else "status:plan-review"
    if s == "In Review":
        return "status:spec-review"
    return "status:spec-draft"


def collect(root, cfg):
    out = {}
    specs = root / cfg["specs_dir"]
    for d in sorted(specs.glob("*/")):
        if d.name.startswith("_") or not (d / "spec.md").exists():
            continue
        fm = read_frontmatter(d / "spec.md")
        labels = {stage_of(d)}
        ai = AI_LABELS.get(fm.get("ai_level", "").strip().lower())
        if ai:
            labels.add(ai)
        shared = fm.get("shared_modules", "").strip().lower()
        if shared in ("có", "co", "yes", "true"):
            labels.add("shared-module")
        elif shared in ("không", "khong", "no", "false"):
            labels.add("-shared-module")  # marker: remove the label
        out[d.name] = labels
    return out


def gh(method, path, token, body=None, url=None):
    req = urllib.request.Request(url or f"{API}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return json.loads(data) if data else None


def list_issues(repo, token):
    issues, page = [], 1
    while True:
        batch = gh("GET", f"/repos/{repo}/issues?labels=sdd&state=all&per_page=100&page={page}", token)
        issues += [i for i in batch if "pull_request" not in i]
        if len(batch) < 100:
            return issues
        page += 1


def graphql(token, query, variables):
    res = gh("POST", "", token, {"query": query, "variables": variables}, url="https://api.github.com/graphql")
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    return res["data"]


class Board:
    """GitHub Projects v2 board owned by a user or an organization."""

    def __init__(self, token, owner, number):
        self.token = token
        q = """query($o:String!,$n:Int!){
          user(login:$o){projectV2(number:$n){id fields(first:50){nodes{... on ProjectV2SingleSelectField{id name options{id name}}}}}}
        }"""
        try:
            p = graphql(token, q, {"o": owner, "n": number})["user"]["projectV2"]
        except Exception:
            q = q.replace("user(login", "organization(login")
            p = graphql(token, q, {"o": owner, "n": number})["organization"]["projectV2"]
        self.project_id = p["id"]
        field = next(f for f in p["fields"]["nodes"] if f and f.get("name") == "Status")
        self.field_id = field["id"]
        self.options = {o["name"]: o["id"] for o in field["options"]}
        missing = [name for _, name in STAGES if name not in self.options]
        if missing:
            print(f"[sdd-sync] WARN board Status field lacks options: {missing}")

    def set_status(self, issue_node_id, option_name):
        if option_name not in self.options:
            return
        item = graphql(self.token, """mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}""",
                       {"p": self.project_id, "c": issue_node_id})["addProjectV2ItemById"]["item"]["id"]
        graphql(self.token, """mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}""",
                {"p": self.project_id, "i": item, "f": self.field_id, "o": self.options[option_name]})


def plan_changes(issues, wanted, id_re, allow_backward):
    """Return [(issue, add_labels, remove_labels, stage_label)]."""
    changes = []
    for issue in issues:
        m = id_re.match(issue["title"].strip())
        if not m:
            continue
        item = f"{m.group('prefix')}-{m.group('num')}"
        if item not in wanted:
            continue
        current = {lbl["name"] for lbl in issue.get("labels", [])}
        new = wanted[item]
        new_stage = next(lbl for lbl in new if lbl.startswith("status:"))
        cur_stages = [lbl for lbl in current if lbl.startswith("status:")]
        cur_rank = max((RANK.get(lbl, -1) for lbl in cur_stages), default=-1)
        terminal = new_stage in ("status:done", "status:dropped")
        # Backward only for a change request merged to main (spec back to Draft / In Review);
        # otherwise main (spec Approved) would pull back an item that is Implementing on its branch.
        reopened = allow_backward and new_stage in ("status:spec-draft", "status:spec-review")
        if RANK[new_stage] < cur_rank and not (reopened or terminal):
            new = {lbl for lbl in new if not lbl.startswith("status:")}
            new_stage = None
        drop = {lbl[1:] for lbl in new if lbl.startswith("-")}
        new = {lbl for lbl in new if not lbl.startswith("-")}
        add = new - current
        remove = {lbl for lbl in cur_stages if new_stage and lbl != new_stage} | (drop & current)
        if add or remove:
            changes.append((issue, sorted(add), sorted(remove), new_stage))
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--issues-json", help="read issues from a file instead of the API (testing)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg = load_config(root)
    id_re = re.compile(cfg["id_regex"])
    wanted = collect(root, cfg)
    print(f"[sdd-sync] specs: {', '.join(f'{k}={sorted(v)}' for k, v in wanted.items()) or 'none'}")

    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if args.issues_json:
        issues = json.loads(Path(args.issues_json).read_text(encoding="utf-8"))
    else:
        if not (token and repo):
            print("[sdd-sync] GITHUB_TOKEN and GITHUB_REPOSITORY are required")
            return 2
        issues = list_issues(repo, token)

    allow_backward = os.environ.get("SDD_ALLOW_BACKWARD") == "1"
    changes = plan_changes(issues, wanted, id_re, allow_backward)
    board = None
    if not args.dry_run and os.environ.get("PROJECT_TOKEN") and os.environ.get("PROJECT_NUMBER"):
        board = Board(os.environ["PROJECT_TOKEN"], os.environ.get("PROJECT_OWNER") or repo.split("/")[0],
                      int(os.environ["PROJECT_NUMBER"]))

    for issue, add, remove, stage in changes:
        print(f"[sdd-sync] #{issue['number']} {issue['title'][:50]!r}: +{add} -{remove}")
        if args.dry_run:
            continue
        n = issue["number"]
        for lbl in remove:
            gh("DELETE", f"/repos/{repo}/issues/{n}/labels/{urllib.request.quote(lbl, safe='')}", token)
        if add:
            gh("POST", f"/repos/{repo}/issues/{n}/labels", token, {"labels": add})
        if board and stage:
            board.set_status(issue["node_id"], BOARD[stage])
    print(f"[sdd-sync] {len(changes)} issue(s) updated{' (dry run)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
