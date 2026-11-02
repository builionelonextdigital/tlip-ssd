#!/usr/bin/env bash
# Tạo nhãn SDD trên repo GitHub (chạy một lần, cần `gh` đã đăng nhập tài khoản có quyền admin repo).
#   ./tools/setup_github.sh
set -euo pipefail

label() { gh label create "$1" --color "$2" --description "$3" --force >/dev/null && echo "  ✓ $1"; }

echo "Nhãn quy trình:"
label "sdd"                   "5319e7" "Hạng mục chạy theo quy trình SDD"
label "status:backlog"        "ededed" "Chưa có spec"
label "status:spec-draft"     "fbca04" "Spec đang soạn"
label "status:spec-review"    "f9d0c4" "Spec chờ FC + TC duyệt"
label "status:spec-approved"  "c2e0c6" "Spec đã duyệt, chưa có plan"
label "status:plan-review"    "bfd4f2" "Plan chờ TC duyệt"
label "status:ready-to-build" "0e8a16" "Spec + plan đã duyệt, sẵn sàng code"
label "status:implementing"   "1d76db" "Đang code"
label "status:done"           "0b6623" "Đã merge và qua UAT"
label "status:dropped"        "b60205" "Hủy"

echo "Nhãn phân loại:"
label "ai:cao"        "d4c5f9" "Mức dùng AI: Cao"
label "ai:trung-binh" "c5def5" "Mức dùng AI: Trung bình"
label "ai:thap"       "e99695" "Mức dùng AI: Thấp – AI không viết logic lõi"
label "shared-module" "d93f0b" "Đụng module dùng chung – cần pod Core review"
label "pod:o2c"       "006b75" "Gói O2C"
label "pod:p2p"       "5a32a3" "Gói P2P"

cat <<'TXT'

Việc làm tay trên GitHub (một lần):
  1. Cài Claude GitHub App: https://github.com/apps/claude  (hoặc chạy /install-github-app trong Claude Code)
  2. Settings → Secrets and variables → Actions:
       Secret ANTHROPIC_API_KEY (hoặc CLAUDE_CODE_OAUTH_TOKEN, sửa claude.yml tương ứng)
  3. Tạo Project (Board) "TLIP SDD", trường Status có đúng các lựa chọn:
       Backlog, Spec Draft, Spec Review, Spec Approved, Plan Review, Ready to build, Implementing, Done, Dropped
     rồi (tùy chọn, để board tự chuyển cột):
       Secret PROJECT_TOKEN = fine-grained PAT có quyền Projects read/write
       Variable PROJECT_OWNER = tài khoản sở hữu project, PROJECT_NUMBER = số của project
     Không cấu hình bước này thì board vẫn lọc/nhóm được theo nhãn status:*.
  4. Branch protection cho main: bắt buộc PR, check "SDD check", 1 approval.
TXT
