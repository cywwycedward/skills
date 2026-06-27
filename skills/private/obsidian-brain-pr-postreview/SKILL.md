---
name: obsidian-brain-pr-postreview
description: >
  处理已存在的 Obsidian brain PR 审核事件：new_comment、review_approved、
  review_changes_requested、merged、closed、reminder。用于轮询脚本输出事件，
  或用户告知 PR 已 approve / merge / close / 要按 review 修改。本地修改、PR 创建、
  path check 和分支同步分别交给 write/config、`obsidian-brain-pr-workflow`、
  `sync-obsidian-brain`。
metadata:
  openclaw:
    emoji: "🛂"
    requires:
      bins: ["git", "gh"]
    os: ["darwin", "linux"]
---

# obsidian-brain-pr-postreview

处理用户审核 obsidian-brain PR 后的异步结果。事件来源有两种：

1. `obsidian-brain-pr-workflow` 启动的后台轮询脚本（`poll-pr-status.sh`）输出的事件行
2. 用户在对话中直接告知审核结果

两种来源的处理规则一致。

## 何时使用

- 收到轮询脚本的事件行
- 用户口头告知 PR review / approve / merge / close 状态
- 需要对已有 PR 做 fix-up commit 回应 review

不适用的场景：

- PR 还没创建 → `obsidian-brain-pr-workflow`
- 本地内容还没改完 → `obsidian-brain-write` / `obsidian-brain-config`
- 与远程 main 同步 → `sync-obsidian-brain`

## 参数

- `pr_number` 或 `pr_url`：目标 PR
- `event_type`：事件类型（见下表）；若来源于用户口头，可由 agent 翻译
- `event_detail`（可选）：评论内容、审核者等

## 本地策略引用

- worktree、权限分类、PR/reset 策略以 workspace `TOOLS.md` 为权威。
- 本 skill 只处理 `openclaw/data` 与 `openclaw/config` 这两个 PR head 分支。
- 对 review 反馈做 fix-up commit 时，仍按 `TOOLS.md` 对本次新增改动重新分类；审阅后允许区必须再次获得用户同意。

## 事件 → 处理映射

| 事件 | 处理动作 |
|------|---------|
| `new_comment` | 读取评论 → 在对应 worktree 改代码 → push → 在 PR 上回复"已修改，请重新审核" |
| `review_changes_requested` | 与 `new_comment` 相同（评论可能附带 diff 建议），但需在回复中显式说明已按 review 要求处理 |
| `review_approved` | **不自动 merge**，告知用户已 approve，等用户手动 merge（或在用户明确同意后才 `gh pr merge`）|
| `merged` | 通知用户已合并；更新 brain worktree 到最新 main；轮询脚本自行退出 |
| `closed`（未 merged） | 视为放弃本次修改：reset 本地 + 远程分支到 origin/main；告知用户已重置 |
| `reminder` | 把"PR 仍在等待审核 N 小时"提醒用户，不做其它动作 |

> 同一 PR 可能有多次 `new_comment`，每次都按上述规则响应。`merged` / `closed` 是终态，处理完成后该 PR 闭环。

## 前置条件

- 处于对应 PR 的 worktree（`brain-edward` 或 `brain-config`）
  - 不在时先 `cd` 到正确路径并校验分支
- `gh auth status` 已登录
- 知道 PR 编号 / URL

## 工作流

### 通用：定位 PR 与 worktree

```bash
gh pr view <pr_number> --json number,url,headRefName,baseRefName,state,merged,files
```

根据 `headRefName` 决定 worktree：

| headRefName | worktree |
|------|------|
| `openclaw/data` | `~/workspace/brain-edward` |
| `openclaw/config` | `~/workspace/brain-config` |
| 其他 | 不属于本 skill 范畴，告知用户 |

```bash
cd <worktree>
git rev-parse --abbrev-ref HEAD   # 应等于 headRefName
git fetch origin <headRefName>
git status --porcelain
```

> 工作区有未知改动 → 暂停，问清来源后再处理。

### Case A: new_comment / review_changes_requested

#### A.1 拉取最新 review 内容

```bash
gh pr view <pr_number> --json comments,reviews
gh api repos/<owner>/<repo>/pulls/<pr_number>/comments  # 行级评论（可选）
```

> 行级评论与 issue-style 评论位置不同，需要时分别拉。优先看 review state 为 `CHANGES_REQUESTED` 或 `COMMENTED` 的最新 review。

#### A.2 同步本地分支到远端最新

```bash
git fetch origin <headRefName>
if ! git pull --ff-only origin <headRefName>; then
  git status --porcelain
  git log --oneline --left-right HEAD...origin/<headRefName> -n 20
  echo "ff-only pull failed; pause and ask the user how to handle local divergence" >&2
  exit 1
fi
```

`--ff-only` 失败说明本地有未推送提交（agent 没人会在此 worktree 自行提交，多半是用户手动改的），暂停并询问用户。

#### A.3 修改代码

按 review 要求修改文件。所有修改仍受 `TOOLS.md` 的权限模型约束：

- 自动允许区 → 可直接修改并追加 commit。
- 审阅后允许区 → **再次**向用户说明本次修改计划并获得同意，即使原 PR 之前已经过用户审阅。
- 禁止区 → 停止，不修改、不暂存、不 push，向用户说明 review 要求与权限冲突。

#### A.4 提交并 push

```bash
git add -A
git diff --cached --name-only   # 自检：仍在允许区内
git commit -m "review: <概括 review 反馈与修改要点>"
git push origin <headRefName>
```

> 这里 push 不带 `--force`。新的 commit 是对原 PR 的追加，不重写历史。

#### A.5 在 PR 上回复

```bash
gh pr comment <pr_number> --body "$(cat <<'EOF'
已按 review 反馈修改：
- <文件1>: <修改要点>
- <文件2>: <修改要点>

请重新审核。
EOF
)"
```

如果 review 是行级评论，理想是在原线程下回复。`gh` CLI 不直接支持 review thread reply，可退化为 issue-style 评论并在 body 中引用 review 要点；或使用：

```bash
gh api -X POST repos/<owner>/<repo>/pulls/<pr_number>/comments/<comment_id>/replies -f body="..."
```

#### A.6 重新进入等待

push 后 path check 会自动重跑。是否需要重新 watch path check：

- 如果原 `obsidian-brain-pr-workflow` 流程已退出（轮询脚本仍在跑），由轮询脚本继续监控；agent 不需要重新 `gh pr checks --watch`
- 如果不确定轮询脚本是否还在，可 `ps aux | grep poll-pr-status.sh | grep <pr>` 确认；不在则重启脚本

### Case B: review_approved

不要自动 merge。即便所有 check 都过。

通知用户：

```
PR #<n> 已被 <reviewer> approve（<url>）。
已在等待你手动 merge；如需我代为执行，请明确说"merge 这个 PR"。
```

只有用户**明确指示** merge 时，才执行：

```bash
gh pr merge <pr_number> --merge
# 成功后更新 brain worktree
cd ~/workspace/brain && git fetch origin main && git merge --ff-only origin/main
```

### Case C: merged

```bash
# 1. 确认 PR 已 merged
gh pr view <pr_number> --json state,merged   # state=MERGED, merged=true

# 2. 更新只读 brain worktree
cd ~/workspace/brain
git fetch origin main
git merge --ff-only origin/main
```

通知用户：

```
PR #<n> 已合并。brain worktree 已更新到最新 main。
```

轮询脚本会在收到 `merged` 后自行退出，无需 agent 处理进程。

### Case D: closed（未 merged）

视为放弃本次修改。**重置本地 + 远程**到 `origin/main`：

#### D.1 校验

```bash
gh pr view <pr_number> --json state,merged,headRefName
# 确认 state=CLOSED 且 merged=false
```

如果 `merged=true`（被 squash 后视为 closed），按 Case C 处理而非本 case。

#### D.2 备份当前分支提示（不强制）

reset 是不可逆操作，先告知用户即将执行的命令，**等用户明确同意**再执行：

```
PR #<n> 已被你 close 且未合并，按"放弃本次修改"处理：
我准备执行（不可逆，请确认）：
  cd <worktree>
  git fetch origin main
  git reset --hard origin/main
  git push --force-with-lease origin <headRefName>
```

> 即使本规则已写明此场景的处理方式，每次执行 reset 仍要把命令展示给用户并等待"OK / 同意 / 执行"等明确确认。

#### D.3 执行重置

用户同意后：

```bash
cd <worktree>
git fetch origin main
git reset --hard origin/main
git push --force-with-lease origin <headRefName>
```

> 用 `--force-with-lease` 而非 `--force`，避免覆盖 close 之后他人在该分支上的提交。

#### D.4 通知

```
分支 <headRefName> 已重置到 origin/main 当前 HEAD。
本地 worktree 与远程分支均已同步。
```

### Case E: reminder

仅提醒，不操作仓库：

```
PR #<n> (<url>) 已 <elapsed>s 没有进展，提醒你抽空 review。
```

> 提醒频率由轮询脚本控制（默认 24 小时一次），agent 不应主动加倍。

## 输出格式

每个事件处理结束后回复用户：

```
[PR #<n>] event: <event_type>
- 处理动作：<一句话>
- 涉及文件：<列表>（如有）
- 后续：<继续等待 / 已结束 / 等用户决策>
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 当前 worktree 与 PR headRefName 不匹配 | 切到正确 worktree；若不存在告知用户 |
| `git pull --ff-only` 失败（本地有领先提交） | 暂停；问用户来源（手动改 / 中途的 fix-up） |
| review comment 内容过长或多条 | 摘要给用户，让用户确认重点；不要在没看清的情况下盲改 |
| Case D 用户没有明确同意 reset | 不执行；等待用户确认 |
| `gh api` 行级评论回复失败 | 退化为 `gh pr comment` issue-style 评论，并显式引用要点 |
| Case A 修改涉及审阅区但未先获用户同意 | 暂停；先列计划等用户同意 |
| 事件中 PR 编号未知 / 已不存在 | 不操作；告知用户事件无效 |
| 同一 PR 收到 `merged` 后又收到事件 | 忽略后续事件（PR 已闭环） |

## 安全约束

- `--force-with-lease` 仅用于 Case D 的 reset；不在其他场景使用
- 不主动 merge：approve 事件下必须等用户明确指示
- Case D 的 reset 命令必须先展示给用户并获明确同意才执行
- 修改审阅区文件时仍需对**本次修改内容**单独获得用户同意
- 不在 PR comment / 任何 GitHub 文本中泄露 MEMORY.md 或私人路径

## 示例

**轮询事件示例**

输入：
```
new_comment|42|alice: 把变量名改成 snake_case
```

处理：
1. `gh pr view 42 --json headRefName` → `openclaw/data`
2. `cd ~/workspace/brain-edward && git fetch origin openclaw/data && git pull --ff-only`
3. 找到对应文件，按 review 要求改名
4. 自检 → `git add -A && git commit -m "review: rename to snake_case" && git push`
5. `gh pr comment 42 --body "已按 review 把变量名改成 snake_case，请重新审核。"`

**Approve 事件**

```
review_approved|42|alice
```

回复用户：

```
PR #42 已被 alice approve。我不会自动 merge，等你确认后告诉我，或你直接在 GitHub 上 merge。
```

**Closed 事件**

```
closed|42|
```

1. `gh pr view 42 --json state,merged` → 确认 CLOSED & merged=false
2. 把 reset 命令展示给用户等同意
3. 用户同意 → 执行 reset + force-with-lease
4. 通知完成
