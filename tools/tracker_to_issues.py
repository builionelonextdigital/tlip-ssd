#!/usr/bin/env python3
"""Create one GitHub Issue per tracker item (sheet "Chi tiết task") for the SDD board.

Runs on a TC's machine (the tracker lives in Project-infomations/, which is not in git).
Default is a dry run that prints what would be created; --apply creates the issues with `gh`.

  python3 tools/tracker_to_issues.py                       # dry run, all items
  python3 tools/tracker_to_issues.py --only O2C --apply    # create O2C items
  python3 tools/tracker_to_issues.py --codes "O2C No. 14" "O2C No. 23" --apply

Only the solution-design columns are copied (problem, solution, how, model/field, notes).
Review the dry-run output before --apply: no real customer data may go into an issue.
Requires: openpyxl, GitHub CLI logged in to the repo's account.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("pip install openpyxl")

SHARED = ("tlip_approval", "tlip_access_rights", "pcv_minvoice", "pcv_mysign",
          "approval.matrix", "minvoice", "mysign")
AI = {"cao": "ai:cao", "trung bình": "ai:trung-binh", "thấp": "ai:thap"}
SECTIONS = [  # (tracker column, issue heading) – same headings as the issue form
    ("Vấn đề / Hiện trạng", "Vấn đề / Hiện trạng"),
    ("Giải pháp", "Giải pháp"),
    ("Cách làm", "Cách làm"),
    ("Model / Field cần sửa", "Model / Field cần sửa"),
]


def read_tracker(path, sheet, id_col):
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and id_col in r)
    head = [str(h).strip() if h else "" for h in rows[hi]]
    items = {}
    for r in rows[hi + 1:]:
        if not r or not r[head.index(id_col)]:
            continue
        d = {h: (str(v).strip() if v is not None else "") for h, v in zip(head, r)}
        items.setdefault(d[id_col], []).append(d)
    return items


def build(code, rows):
    main = max(rows, key=lambda d: sum(bool(v) for v in d.values()))  # fullest row first
    title_name = next((d.get("Task / Hạng mục") for d in rows if d.get("Task / Hạng mục")), "")
    ai_raw = next((d.get("Mức dùng AI") for d in rows if d.get("Mức dùng AI")), "")
    text_all = " ".join(" ".join(d.values()) for d in rows).lower()
    hits = sorted({s for s in SHARED if s in text_all})
    shared = f"Chưa rõ – tracker có nhắc tới: {', '.join(hits)} (spec sẽ chốt)" if hits else "Chưa rõ"
    md = main.get("MD", "")

    parts = [
        "### Mã hạng mục", "", code, "",
        "### Mức dùng AI", "", ai_raw or "_Chưa có trong tracker_", "",
        "### Có đụng module dùng chung? (tlip_approval, tlip_access_rights, pcv_minvoice, pcv_mysign)", "", shared, "",
        "### MD ước lượng", "", md or "_Chưa có_", "",
    ]
    for col, heading in SECTIONS:
        parts += [f"### {heading}", "", main.get(col) or "_Chưa có_", ""]
    notes = [f"- Pod: {main.get('Pod', '')} · {main.get('Nhóm / Đợt', '')} · Thời gian: {main.get('Thời gian', '')}"]
    for key in ("Gợi ý dùng AI", "Căn cứ / File", "Ghi chú"):
        if main.get(key):
            notes.append(f"- {key}: {main[key]}")
    for i, extra in enumerate(r for r in rows if r is not main):
        notes.append(f"- **Tracker có thêm dòng trùng mã #{i + 2}** (FC chốt dòng nào là nguồn):")
        for col, heading in SECTIONS + [("Ghi chú", "Ghi chú")]:
            if extra.get(col) and extra.get(col) != main.get(col):
                notes.append(f"    - {heading}: " + extra[col].replace("\n", "\n      "))
    parts += ["### Ghi chú / Căn cứ (tài liệu, biên bản họp)", "", "\n".join(notes), "",
              "---", "_Tạo từ TLIP_Phase_Tracker.xlsx. Comment `@claude /sdd-spec` để soạn spec._"]

    labels = ["sdd", "status:backlog"]
    if AI.get(ai_raw.lower()):
        labels.append(AI[ai_raw.lower()])
    prefix = code.split()[0].lower()
    labels.append(f"pod:{prefix}")
    title = f"[{code}] {title_name}".strip()
    return title, "\n".join(parts), labels


def existing_codes(id_re):
    out = subprocess.run(["gh", "issue", "list", "--label", "sdd", "--state", "all", "--limit", "1000",
                          "--json", "title"], check=True, capture_output=True, text=True).stdout
    codes = set()
    for issue in json.loads(out):
        m = id_re.match(issue["title"])
        if m:
            codes.add(f"{m.group('prefix')}-{m.group('num')}")
    return codes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tracker", default="Project-infomations/TLIP_Phase_Tracker.xlsx")
    ap.add_argument("--sheet", default="Chi tiết task")
    ap.add_argument("--id-col", default="Mã")
    ap.add_argument("--only", help="prefix filter, e.g. O2C or P2P")
    ap.add_argument("--codes", nargs="*", help="exact codes, e.g. 'O2C No. 14'")
    ap.add_argument("--apply", action="store_true", help="create the issues (default: dry run)")
    ap.add_argument("--show-body", action="store_true", help="print full issue bodies in dry run")
    args = ap.parse_args()

    id_re = re.compile(r"^\[(?P<prefix>[A-Z][A-Z0-9]+)(?: No\.)? ?#?(?P<num>\d+)\]")
    items = read_tracker(args.tracker, args.sheet, args.id_col)
    if args.only:
        items = {k: v for k, v in items.items() if k.startswith(args.only)}
    if args.codes:
        items = {k: v for k, v in items.items() if k in args.codes}

    have = existing_codes(id_re) if args.apply else set()
    created = skipped = 0
    for code, rows in items.items():
        title, body, labels = build(code, rows)
        key = id_re.match(title)
        key = f"{key.group('prefix')}-{key.group('num')}" if key else code
        if key in have:
            print(f"= {title[:70]}  (đã có issue, bỏ qua)")
            skipped += 1
            continue
        dup = f"  [tracker có {len(rows)} dòng trùng mã]" if len(rows) > 1 else ""
        print(f"{'+' if args.apply else '?'} {title[:70]}  {labels}{dup}")
        if args.show_body and not args.apply:
            print("    " + body.replace("\n", "\n    ") + "\n")
        if args.apply:
            subprocess.run(["gh", "issue", "create", "--title", title, "--body", body,
                            *sum([["--label", lbl] for lbl in labels], [])], check=True)
            created += 1
    mode = "đã tạo" if args.apply else "sẽ tạo (dry run, thêm --apply để tạo)"
    print(f"\n{len(items) - skipped} issue {mode}; bỏ qua {skipped}.")


if __name__ == "__main__":
    main()
