---
name: obsidian-brain-pr-workflow
description: >
  将已完成的 Obsidian 知识库本地修改提交为 PR：commit、完整 outgoing diff
  权限检查、普通 push、创建 PR、watch path check，并按范围自动 merge 或等待用户审核。
  由 `obsidian-brain-write` / `obsidian-brain-config` 在本地修改后调用；用户要求提交
  brain PR 或 push 知识库改动时也使用。本地修改阶段、PR 后续事件和分支同步分别交给
  write/config、`obsidian-brain-pr-postreview`、`sync-obsidian-brain`。
metadata:
  openclaw:
    emoji: "🚀"
    requires:
      bins: ["git", "gh", "bash"]
    files: ["scripts/*"]
    os: ["darwin", "linux"]
---

# obsidian-brain-pr-workflow

封装知识库修改后的同步 PR 流程：把本地 worktree 已经准备好的修改打包成一个 PR，watch path check，再决策"自动 merge"或"等用户审核"。

## 何时使用

- `obsidian-brain-write` 完成本地修改后调用
- `obsidian-brain-config` 完成本地修改后调用
- 用户明确要求提交 PR

不适用的场景：

- 本地修改还没做完 → 先回到 `obsidian-brain-write` / `obsidian-brain-config`
- PR 已经创建、需要响应审核事件 → 用 `obsidian-brain-pr-postreview`
- 与远程 main 同步 → 用 `sync-obsidian-brain`

## 参数

调用方需传入：

- `worktree_path`：`~/workspace/brain-edward` 或 `~/workspace/brain-config`
- `branch`：`openclaw/data` 或 `openclaw/config`

未显式传入时，可从 `pwd` 与 `git rev-parse --abbrev-ref HEAD` 推断；推断结果与允许集合不符则中止。

## 前置条件

- 处于上述两个 worktree 之一
- 当前分支与上表对应正确
- `git status --porcelain` 显示要么有待提交修改，要么已经在合适的 commit 上（即工作区干净且 HEAD 包含未 push 的本次修改）
- `gh auth status` 已登录
- 本机存在 `scripts/poll-pr-status.sh` 并可执行；脚本只依赖 `bash` 与 `gh`

## 本地策略引用

- worktree、权限分类、PR 策略以 workspace `TOOLS.md` 为权威。
- 本 skill 只处理 `~/workspace/brain-edward` / `openclaw/data` 或 `~/workspace/brain-config` / `openclaw/config`。
- "自动 merge" 仅当完整 PR diff 完全落在 `TOOLS.md` 定义的自动允许区，且 checks 全过时适用；`brain-config` 没有自动允许区。

## 工作流

### Phase 1: 提交与推送

#### 1.1 校验 worktree 与分支

```bash
cd <worktree_path>
pwd
git rev-parse --abbrev-ref HEAD   # 必须等于 <branch>
```

不匹配立即中止，告知用户。

#### 1.2 暂存并核查权限

```bash
git add -A
git diff --cached --name-only
```

把暂存文件清单逐项匹配到 worktree 对应的允许集合：

- 暂存清单中存在**禁止区**文件（如 brain-edward 暂存了 `.obsidian/`，或 brain-config 暂存了 `edward/`）：
  ```bash
  git reset HEAD
  ```
  立即中止，列出违规文件并告知用户。**不要**自行 `git restore` 这些文件——可能是用户故意保留的本地状态，决定权交还用户。

- 全部在允许集合内 → 继续。

#### 1.3 提交

如果 `git diff --cached --quiet` 显示有暂存改动：

```bash
git commit -m "<根据修改生成的简短描述>"
```

commit 信息要求：

- 一句话陈述修改的"是什么、在哪里"，不超过 70 字符标题；正文（可选）说明"为什么"
- 不写 `[skip ci]`、`--no-verify`、`Co-authored-by` 等绕过 / 冒充字样
- 涉及多个目录的修改在正文中分项列出

如果暂存为空但 HEAD 已经包含未推送的本次修改（调用方在更早阶段已经 commit），跳过 commit 直接进入 1.4。

#### 1.4 完整 PR scope gate

push 前必须检查 `origin/main...HEAD` 的完整 outgoing diff，而不是只看本轮 staged files；这样工作区干净但 HEAD 已有未推送提交时也不能绕过路径权限。

```bash
git fetch origin main
git diff --name-only origin/main...HEAD
```

把完整文件清单逐项匹配到 worktree 对应的允许集合：

- 存在**禁止区**文件 → 中止，不 push，不 restore，列出违规文件并交还用户处理。
- 存在**审阅区**文件 → 确认 write/config 阶段已获得用户对本次具体修改的同意；没有同意记录则暂停，补充说明改动计划并等待用户明确同意。
- 全部在允许集合内，且审阅区同意记录齐全 → 继续。

> 这个 gate 是推送前最后一道本地权限检查；后续 GitHub path check 仍会再验证一次。

#### 1.5 推送

```bash
git push origin <branch>
```

首次推送或上游缺失时使用 `git push -u origin <branch>`。**禁止 `--force`**，本阶段 force push 一律视为异常。

### Phase 2: 创建 PR

#### 2.1 生成 PR 描述

按以下模板组织 PR body（用 here-doc 传给 `gh`）：

```
## 修改内容
- <path1>: <一句话说明>
- <path2>: <一句话说明>

## 权限范围
- 自动区: <文件列表，可写"无"或留空段>
- 审阅区: <文件列表，可写"无"或留空段>

## 审核状态
- <若 write/config 阶段已获用户对审阅区内容的同意，在此注明，例如：用户已对 atari/journals/2026-05.md 的错别字修改同意>
- <自动区无需此项>
```

#### 2.2 创建 PR

```bash
gh pr create \
  --base main \
  --head <branch> \
  --title "<简短标题，<= 70 字符>" \
  --body "$(cat <<'EOF'
<上面的 body>
EOF
)"
```

记录 `gh pr create` 输出的 PR URL 与 number，后续步骤复用。

如果 `gh pr create` 返回"there is already a PR"，改为：

```bash
gh pr view <branch> --json number,url,headRefName
```

复用已存在的 PR；并把这次新增的 commits 视作对原 PR 的更新。

### Phase 3: Watch Path Check

```bash
gh pr checks <pr_number> --watch
```

> `gh pr checks --watch` 会阻塞到所有 check 终态。第一层（path check）属 GitHub Actions 范畴。第二层（CODEOWNERS）以"reviewers required"形式存在，**不属于 checks**，不需要在此 watch。

退出后判断：

- 全部 `pass` → Phase 4
- 出现 `fail` → Phase 5
- 出现 `error`（非业务失败，如 runner 异常 / 网络） → Phase 5 的"非路径问题"分支

### Phase 4: 判断文件范围并决策

#### 4.1 拉取 PR 修改文件清单

```bash
gh pr diff <pr_number> --name-only
```

#### 4.2 分支决策

| 修改范围 | 行为 |
|---------|------|
| **完全在自动允许区** | 进入 4.3 自动 merge |
| **包含审阅区或其他区域** | 进入 4.4 启动轮询并通知用户 |

> brain-config 没有自动允许区，凡是来自 brain-config 的 PR 一律走 4.4。

#### 4.3 自动 merge（仅自动允许区）

满足以下**全部**条件才执行：

1. Phase 3 的所有 checks 全部通过
2. 所有修改文件均在 `edward/` 或 `.wiki/` 内
3. 不涉及任何审阅区或禁止区文件

执行：

```bash
gh pr merge <pr_number> --merge
```

> 使用 `--merge`（不是 `--squash` / `--rebase`），保留分支提交历史。

##### 4.3.1 处理 merge 冲突

`gh pr merge` 失败提示存在冲突时：

```bash
git fetch origin main
git merge origin/main
```

判断冲突文件归属：

- **冲突文件全部在自动允许区** → agent 自行解决冲突 → `git push origin <branch>` → 回到 4.3 重试 `gh pr merge`
- **冲突涉及审阅区或禁止区** → agent **不自行解决**，列出冲突文件与冲突段落给用户，等待用户决策；告知后切换到等待模式（不启动轮询，因为还没回到可 merge 状态，用户决策后再回到本 phase）

##### 4.3.2 merge 成功后更新 brain worktree

把只读 brain 跟到最新的 main：

```bash
cd ~/workspace/brain
git fetch origin main
git merge --ff-only origin/main
```

`--ff-only` 失败说明 brain worktree 状态异常（不应该自行变更 main），告知用户但不自动处理。

#### 4.4 启动轮询脚本（需要用户审核时）

```bash
SCRIPT="<本 skill 路径>/scripts/poll-pr-status.sh"
nohup bash "$SCRIPT" <pr_number> > /tmp/obsidian-brain-pr-<pr_number>.log 2>&1 &
disown
```

> 脚本以后台进程形式独立运行，输出事件按行写入日志文件；agent 在后续会话中可读 log 或直接接受用户口头反馈。

通知用户：

```
PR 已创建，path check 通过：<pr_url>

需要你的审核：本次修改包含 <审阅区文件列表>。
请在 GitHub 上 review；approve 后告诉我，或直接在 PR 上 comment / merge / close，
我会通过轮询脚本捕获状态变化并继续处理。
```

PR 状态变化的处理委托给 `obsidian-brain-pr-postreview`。

### Phase 5: Path Check 失败修复

#### 5.1 取详情并分类

```bash
gh pr checks <pr_number> --json name,state,detailsUrl
```

读取失败 check 的日志（必要时 `gh run view <run_id> --log-failed`）：

| 失败类型 | 表现 | 处理 |
|---------|------|------|
| **路径违规** | check 输出明确指出某文件不在允许目录 | 进入 5.2 |
| **非路径问题** | runner 故障、网络超时、脚本本身报错（与本次 diff 无关） | **不自动重试**；告知用户失败原因与日志链接，等待用户判断（重新触发 / 修脚本 / 忽略） |

> 不要把"非路径问题"误判为"路径违规"去乱删文件。**先看 check 日志再行动。**

#### 5.2 修复路径违规

1. 找到违规文件（用 5.1 拿到的清单 + `gh pr diff <pr_number> --name-only` 比对）
2. 在本地 worktree 中恢复 / 删除这些文件：
   ```bash
   # 来自上一个版本（恢复到 origin/main 上的状态）
   git checkout origin/main -- <path>
   # 或者完全删除新增的违规文件
   git rm <path>
   ```
3. 提交修复：
   ```bash
   git add -A
   git commit -m "fix: address path check failures (<违规路径概要>)"
   ```
4. 追加修复 commit 更新 PR：
   ```bash
   git push origin <branch>
   ```
	   > 该修复是追加 commit，不重写历史；默认禁止历史重写。
5. 回到 Phase 3 重新 watch

## 输出格式

每个 phase 结束时给用户一条简短状态：

```
[PR #<n>] phase: <commit-push|create|watch|merge|wait-review|fix>
- <一句话状态说明>
- <下一步>
```

最终结束时（merge 完成或进入等待模式）：

```
## PR 状态
- 编号：#<n>
- URL：<url>
- 范围：自动区 / 含审阅区
- 结果：merged / 等待审核（轮询进程 PID=<pid>，日志=<log path>）

## 后续
- 已 merged：本地分支保留，brain worktree 已 ff 到最新 main
- 等待审核：用户在 GitHub 操作即可，状态变化由轮询脚本捕获
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 当前 worktree / 分支与参数不匹配 | 中止；告知用户，避免在错分支提交 |
| 暂存清单含禁止区文件 | `git reset HEAD` 取消暂存，列出违规文件，中止 |
| 完整 outgoing diff 含禁止区文件 | 中止；不 push，列出违规文件并交还用户处理 |
| 完整 outgoing diff 含审阅区但缺少本次同意记录 | 暂停；补充说明改动计划并等待用户明确同意 |
| `git push` 被远端拒绝（non-fast-forward 等） | 暂停；告知用户原因，建议先 `sync-obsidian-brain` |
| `gh pr create` 报"already exists" | 改用 `gh pr view <branch>` 取得既有 PR 编号继续 |
| `gh pr checks --watch` 因网络中断退出 | 重试一次；持续失败则告知用户检查网络 / `gh auth` |
| Phase 4 自动 merge 冲突涉及审阅区 / 禁止区 | 不自行解决；列冲突文件等用户决策 |
| Phase 5 失败属于"非路径问题" | 不自动重试；附带日志链接给用户 |
| 轮询脚本启动失败（缺执行权限 / 缺 bash） | 告知用户具体原因；提示 `chmod +x scripts/poll-pr-status.sh` |

## 安全约束

- `--force` / `--force-with-lease` 禁止用于常规 PR 提交与修复流程；只有明确需要重写历史的 reset / rebase 场景才可使用，且必须先展示精确命令、目标分支和原因，等待用户明确同意
- 永远不在 `main` 分支上 commit / push
- push 前必须通过 `origin/main...HEAD` 完整 outgoing diff 权限检查
- 自动 merge 仅适用于全自动允许区且 checks 全过的 PR
- 自动解决 merge 冲突仅适用于冲突文件全部在自动允许区
- 不在 PR body 中包含 MEMORY.md 内容或私人路径（不要把 `~/...` 路径泄到 PR body）
- 轮询脚本运行在后台用户进程，不要 root，不接外网（仅 `gh` API）

## 示例

**自动 merge 场景**

```
1. 校验 worktree=brain-edward / branch=openclaw/data
2. git add -A → diff --cached --name-only 全部在 edward/
3. git commit -m "edward: add RSC research notes"
4. git diff --name-only origin/main...HEAD 全部在 edward/ → git push
5. gh pr create --base main --head openclaw/data ...
6. gh pr checks --watch  → 全过
7. gh pr diff --name-only 全在 edward/ → 自动 merge
8. gh pr merge <n> --merge → 成功
9. cd ~/workspace/brain && git fetch && git merge --ff-only origin/main
```

**等待审核场景**

```
1. 校验 worktree=brain-config / branch=openclaw/config
2. commit & push
3. gh pr create
4. gh pr checks --watch → 全过
5. gh pr diff --name-only 含 .obsidian/appearance.json → 走审核分支
6. nohup bash scripts/poll-pr-status.sh <n> > /tmp/...log 2>&1 &
7. 通知用户审核 PR；状态变化由 obsidian-brain-pr-postreview 处理
```

**path check 失败修复**

```
1. gh pr checks --json ... → 看到 path-check failed，日志指 README.md 不允许
2. git checkout origin/main -- README.md（还原）
3. git commit -m "fix: address path check failures (README.md)"
4. git push origin <branch>
5. 回到 Phase 3 重新 watch
```

## 相关文件

- `scripts/poll-pr-status.sh`：后台轮询脚本，监控 PR 状态变化并写出事件行
