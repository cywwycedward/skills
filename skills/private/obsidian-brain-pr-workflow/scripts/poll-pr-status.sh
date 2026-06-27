#!/usr/bin/env bash
# poll-pr-status.sh — 后台轮询单个 PR 的状态变化，按行输出事件供 agent 消费。
#
# Usage:
#   poll-pr-status.sh <pr_number> [--repo <owner/repo>] [--interval <sec>] [--reminder <sec>]
#
# 输出（一行一事件）：
#   new_comment|<pr_number>|<author>: <comment body 单行截断>
#   review_approved|<pr_number>|<reviewer>
#   review_changes_requested|<pr_number>|<reviewer>
#   merged|<pr_number>|
#   closed|<pr_number>|
#   reminder|<pr_number>|<elapsed seconds since last change>
#
# 终止条件：
#   - PR state 为 MERGED 或 CLOSED → 输出对应事件后退出 0
#   - 收到 SIGTERM / SIGINT → 退出 0
#
# 设计：
#   - 用 `gh pr view --json ... --jq ...` 拉 PR 终态
#   - 用 GitHub REST API 拉 issue comments / reviews 的 numeric ID，分页时先 slurp 再统一计算
#   - 评论与 review 的"新增"基于本地状态文件中记录的最大 numeric ID 判断，避免重复
#   - 状态文件存放在 ${TMPDIR:-/tmp}/obsidian-brain-pr-<pr>.state，重启后可继续

set -euo pipefail

PR=""
REPO=""
INTERVAL=60          # 默认 60s 轮询一次
REMINDER_AFTER=86400 # 24h 无变化提醒一次

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)     REPO="$2"; shift 2;;
    --interval) INTERVAL="$2"; shift 2;;
    --reminder) REMINDER_AFTER="$2"; shift 2;;
    -h|--help)
      sed -n '2,30p' "$0"; exit 0;;
    -*)
      echo "unknown option: $1" >&2; exit 2;;
    *)
      if [[ -z "$PR" ]]; then PR="$1"; else echo "unexpected arg: $1" >&2; exit 2; fi
      shift;;
  esac
done

if [[ -z "$PR" ]]; then
  echo "usage: $0 <pr_number> [--repo owner/repo] [--interval sec] [--reminder sec]" >&2
  exit 2
fi

if ! command -v gh >/dev/null; then
  echo "gh CLI not found" >&2; exit 3
fi

PR_REPO_ARG=()
if [[ -n "$REPO" ]]; then PR_REPO_ARG=(--repo "$REPO"); fi

api_endpoint() {
  local path="$1"
  if [[ -n "$REPO" ]]; then
    printf 'repos/%s/%s\n' "$REPO" "$path"
  else
    printf 'repos/{owner}/{repo}/%s\n' "$path"
  fi
}

fetch_pr_state() {
  gh pr view "$PR" "${PR_REPO_ARG[@]}" --json state,merged --jq '[.state, (.merged | tostring)] | @tsv'
}

max_comment_id() {
  gh api "$(api_endpoint "issues/$PR/comments")" --paginate --slurp --jq '[.[][] | .id] | max // 0'
}

max_review_id() {
  gh api "$(api_endpoint "pulls/$PR/reviews")" --paginate --slurp --jq '[.[][] | .id] | max // 0'
}

list_new_comments() {
  local last="${1:-0}"
  gh api "$(api_endpoint "issues/$PR/comments")" --paginate --slurp --jq ".[][] | select(.id > $last) | [.id, (.user.login // \"unknown\"), (.body // \"\")] | @tsv"
}

list_new_reviews() {
  local last="${1:-0}"
  gh api "$(api_endpoint "pulls/$PR/reviews")" --paginate --slurp --jq ".[][] | select(.id > $last) | [.id, (.user.login // \"unknown\"), (.state // \"\"), (.body // \"\")] | @tsv"
}

STATE_DIR="${TMPDIR:-/tmp}"
STATE_FILE="$STATE_DIR/obsidian-brain-pr-$PR.state"
# 状态文件格式（每行 key=value）：
#   state=OPEN|MERGED|CLOSED
#   last_comment_id=<int>
#   last_review_id=<int>
#   last_change_ts=<unix-seconds>

read_state() {
  local key="$1" default="${2:-}"
  if [[ -f "$STATE_FILE" ]]; then
    awk -F= -v k="$key" '$1==k {print $2; found=1; exit} END{if(!found) exit 1}' "$STATE_FILE" 2>/dev/null || echo "$default"
  else
    echo "$default"
  fi
}

write_state() {
  local tmp
  tmp="$(mktemp "$STATE_FILE.XXXXXX")"
  {
    echo "state=$1"
    echo "last_comment_id=$2"
    echo "last_review_id=$3"
    echo "last_change_ts=$4"
  } > "$tmp"
  mv "$tmp" "$STATE_FILE"
}

emit() {
  # event|pr|detail — 单行；body 中的换行替换为空格，限制长度
  local event="$1" detail="${2:-}"
  detail="${detail//$'\n'/ }"
  detail="${detail//$'\r'/ }"
  # 截断到 200 字符
  if [[ ${#detail} -gt 200 ]]; then detail="${detail:0:197}..."; fi
  printf '%s|%s|%s\n' "$event" "$PR" "$detail"
}

now() { date -u +%s; }

trap 'exit 0' INT TERM

# 初始化：若状态文件不存在，先取一次基线（不发出事件，避免误报历史评论）
init_baseline() {
  local state_line
  if ! state_line="$(fetch_pr_state 2>/dev/null)"; then
    return 1
  fi
  local state max_c max_r
  IFS=$'\t' read -r state _ <<< "$state_line"
  max_c="$(max_comment_id 2>/dev/null)" || return 1
  max_r="$(max_review_id 2>/dev/null)" || return 1
  write_state "$state" "$max_c" "$max_r" "$(now)"
}

if [[ ! -f "$STATE_FILE" ]]; then
  if ! init_baseline; then
    echo "failed to initialize PR baseline (gh view failed)" >&2
    exit 4
  fi
fi

while :; do
  if ! state_line="$(fetch_pr_state 2>/dev/null)"; then
    # gh 偶发失败，不视作变化；下一轮重试
    sleep "$INTERVAL"; continue
  fi

  prev_state="$(read_state state OPEN)"
  prev_max_c="$(read_state last_comment_id 0)"
  prev_max_r="$(read_state last_review_id 0)"
  prev_change_ts="$(read_state last_change_ts "$(now)")"

  IFS=$'\t' read -r cur_state merged <<< "$state_line"

  changed=0

  # 新评论
  while IFS=$'\t' read -r cid author body; do
    [[ -z "$cid" || "$cid" == "null" ]] && continue
    emit "new_comment" "$author: $body"
    if (( cid > prev_max_c )); then prev_max_c="$cid"; fi
    changed=1
  done < <(list_new_comments "${prev_max_c:-0}" 2>/dev/null || true)

  # 新 review
  while IFS=$'\t' read -r rid author rstate body; do
    [[ -z "$rid" || "$rid" == "null" ]] && continue
    case "$rstate" in
      APPROVED)
        emit "review_approved" "$author"
        ;;
      CHANGES_REQUESTED)
        emit "review_changes_requested" "$author: $body"
        ;;
      COMMENTED)
        emit "new_comment" "$author (review): $body"
        ;;
      *)
        # DISMISSED / PENDING 等忽略
        ;;
    esac
    if (( rid > prev_max_r )); then prev_max_r="$rid"; fi
    changed=1
  done < <(list_new_reviews "${prev_max_r:-0}" 2>/dev/null || true)

  # 终态
  if [[ "$cur_state" != "$prev_state" ]]; then
    case "$cur_state" in
      MERGED)
        emit "merged" ""
        write_state "$cur_state" "$prev_max_c" "$prev_max_r" "$(now)"
        exit 0
        ;;
      CLOSED)
        if [[ "$merged" == "true" ]]; then
          emit "merged" ""
        else
          emit "closed" ""
        fi
        write_state "$cur_state" "$prev_max_c" "$prev_max_r" "$(now)"
        exit 0
        ;;
      *)
        changed=1
        ;;
    esac
  fi

  # 提醒
  if [[ $changed -eq 0 ]]; then
    elapsed=$(( $(now) - prev_change_ts ))
    if (( elapsed >= REMINDER_AFTER )); then
      emit "reminder" "$elapsed"
      prev_change_ts="$(now)"
    fi
    write_state "$cur_state" "$prev_max_c" "$prev_max_r" "$prev_change_ts"
  else
    write_state "$cur_state" "$prev_max_c" "$prev_max_r" "$(now)"
  fi

  sleep "$INTERVAL"
done
