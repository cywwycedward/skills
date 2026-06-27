---
name: sync-obsidian-brain
description: >
  同步 obsidian-brain 的 `openclaw/data` 与 `openclaw/config` 工作分支到远程
  `main`：检查未提交内容，区分已同步、远程领先、本地领先、分叉并按策略处理。
  用于 `obsidian-brain-sync.service` 提醒、用户要求同步 brain、查看工作分支与
  main 差异或把工作分支跟上 main。PR 提交、本地写入和只读查阅分别交给
  `obsidian-brain-pr-workflow`、write/config、`obsidian-brain-research`。
metadata:
  openclaw:
    emoji: "🔄"
    requires:
      bins: ["git", "gh"]
    os: ["darwin", "linux"]
---

# sync-obsidian-brain

把 `openclaw/data`（在 `brain-edward` worktree）和 `openclaw/config`（在 `brain-config` worktree）这两个工作分支与远程 `main` 保持一致。

## 何时使用

- Ubuntu user service `obsidian-brain-sync.service` 检测到远程 main 有新提交并通知 agent
- 用户主动要求同步两个工作分支
- 在 `obsidian-brain-write` / `obsidian-brain-config` 启动时发现 `--ff-only` 失败，被建议先 sync

不适用的场景：

- 单个 PR 的合并 / 审核（用 `obsidian-brain-pr-workflow` / `obsidian-brain-pr-postreview`）
- 修改 main 分支本身（**本 skill 永不写入 main**）

## 前置条件

- 三个 worktree 均存在：`~/workspace/brain`、`~/workspace/brain-edward`、`~/workspace/brain-config`
- `git`、`gh` 可用且 `gh auth status` 已登录

## 处理范围

| Worktree | 分支 | 本 skill 是否操作 |
|------|------|------|
| `~/workspace/brain` | `main` | 仅 `git fetch` 和 `git merge --ff-only origin/main`（不写入提交） |
| `~/workspace/brain-edward` | `openclaw/data` | 完整同步流程 |
| `~/workspace/brain-config` | `openclaw/config` | 完整同步流程 |

> 本 skill **不在 main 分支创建任何 commit / push**。

## 工作流

对 `openclaw/data` 与 `openclaw/config` 两个分支**分别**执行下面的步骤；逐个分支串行处理，避免互相干扰。

### Step 1: 切到对应 worktree 并校验

```bash
cd <worktree>     # brain-edward 或 brain-config
pwd
git rev-parse --abbrev-ref HEAD   # 应等于对应分支
```

校验失败 → 报告该 worktree 状态异常，跳过此分支继续下一个；不要试图自动切分支。

### Step 2: 检查未提交内容

```bash
git status --porcelain
```

#### 2.1 没有未提交内容

跳过到 Step 3。

#### 2.2 有未提交内容

```bash
git add -A
git diff --cached --name-only
```

把暂存清单按 workspace `TOOLS.md` 的权限模型分类。

判断：

- **暂存全部在自动允许区**（仅 brain-edward 的 `edward/` / `.wiki/`）→ 自动 commit：
  ```bash
  git commit -m "wip: auto-save before sync"
  ```
- **暂存涉及审阅区** → 暂停 sync；列出审阅区文件给用户，问：是否同意 auto-commit 这些改动？同意才 commit；不同意则中止本分支同步并提醒用户先手动处理。
- **暂存超出允许集合**（出现禁止区文件）→ `git reset HEAD` 取消暂存，**中止本分支同步**，告知用户具体违规文件。

### Step 3: 拉取远程 main

```bash
git fetch origin main
```

### Step 4: 判断同步状态

用 `git rev-list --left-right --count` 一次拿到差异：

```bash
git rev-list --left-right --count HEAD...origin/main
# 输出 "<ahead>\t<behind>"，即本地领先数 \t 远程领先数
```

四种状态：

| ahead | behind | 状态 | 处理 |
|------:|------:|------|------|
| 0 | 0 | **已同步** | 无操作，结束本分支 |
| 0 | >0 | **远程领先** | Step 5 |
| >0 | 0 | **本地领先** | Step 6 |
| >0 | >0 | **分叉** | Step 7 |

### Step 5: 远程领先 → Fast-forward

```bash
git merge --ff-only origin/main
```

`--ff-only` 在此场景理论上不会失败（`behind > 0` 且 `ahead == 0`）；若意外失败，按"分叉"处理（重新评估状态）。

成功后告知用户：

```
[<branch>] 远程领先 N 个提交，已 ff-merge 到最新 main。
```

### Step 6: 本地领先 → 审阅决策

#### 6.1 审阅本地领先提交

```bash
git log origin/main..HEAD --oneline
git diff origin/main..HEAD --stat
```

#### 6.2 询问用户

把 commits 概要与 diff stat 展示给用户，问：

```
分支 <branch> 比 origin/main 领先 N 个提交：
<commits 列表与 stat>

如何处理？
- 保留 → 我会停在这里；后续请你自行 push / 走 PR 流程（或让我用 obsidian-brain-pr-workflow 提交）
- 不保留 → 我会执行：
    git reset --hard origin/main
    git push --force-with-lease origin <branch>
  这是不可逆操作，请明确同意后再执行。
```

#### 6.3 按用户决策执行

- **保留** → 不动，结束本分支同步。如果用户接着说"那帮我提交 PR"，转到 `obsidian-brain-pr-workflow`。
- **不保留**（用户明确同意 reset） →
  ```bash
  git reset --hard origin/main
  git push --force-with-lease origin <branch>
  ```
  完成后告知用户。

### Step 7: 分叉 → 合并或重置

#### 7.1 审阅双方独有提交

```bash
# 本地有而远程没有
git log origin/main..HEAD --oneline
git diff origin/main..HEAD --stat
# 远程有而本地没有
git log HEAD..origin/main --oneline
git diff HEAD..origin/main --stat
```

#### 7.2 询问用户

把双侧 commits 与 stat 展示给用户，问：

```
分支 <branch> 与 origin/main 已分叉：
- 本地领先：N 个提交（<列表>）
- 远程领先：M 个提交（<列表>）

如何处理？
- 保留本地改动 → 我会执行 git merge origin/main，处理冲突；
  - 冲突全部在自动允许区，我自行解决
  - 冲突涉及审阅区 / 禁止区，停下来等你决策
  合并完成后我会调用 obsidian-brain-pr-workflow 把结果走 PR 流程。
- 不保留本地改动 → 我会执行：
    git reset --hard origin/main
    git push --force-with-lease origin <branch>
  这是不可逆操作，请明确同意后再执行。
```

#### 7.3 按用户决策执行

##### 7.3.1 保留本地改动 → 合并

```bash
git merge origin/main
```

| 合并结果 | 处理 |
|---------|------|
| 无冲突，自动产生 merge commit | 进入 7.3.3 |
| 冲突文件**全部**在自动允许区 | agent 自行解决；选择保留本地新写的内容为主，结合远程 main 的更新；解决后 `git add` 各文件 → `git commit`（保留默认 merge 信息或写明"merge origin/main into <branch>"）→ 进入 7.3.3 |
| 冲突涉及审阅区 / 禁止区 | **不自行解决**；列出冲突文件与冲突段落给用户；用户决策后再续：用户给出方案 → 按方案解决并 `git commit` → 进入 7.3.3。如果用户决定放弃合并：`git merge --abort`，再回到 7.2 重新选择"不保留" |

##### 7.3.2 合并后再校验权限

```bash
git diff origin/main...HEAD --name-only
```

如果合并结果中包含**当前 worktree 不该写入的文件**（例如 brain-edward 的 merge 结果意外携带 `.obsidian/`），停下来告知用户；不要把违规结果 push 出去。**通常**这种情况源自原本就在本地领先里的违规提交，需要用户手工调整。

##### 7.3.3 走 PR 流程

```bash
git push origin <branch>
```

然后调用 `obsidian-brain-pr-workflow`（worktree_path / branch 与本步一致）。**不要在 sync skill 里直接 merge 到 main**——任何对 main 的更新都必须经过 PR + path check + CODEOWNERS 流程。

##### 7.3.4 不保留本地改动（用户明确同意 reset）

```bash
git reset --hard origin/main
git push --force-with-lease origin <branch>
```

完成后告知用户。

### Step 8: 同步只读 brain worktree

两个分支处理完后，把 `~/workspace/brain` 也跟到最新 main：

```bash
cd ~/workspace/brain
git fetch origin main
git merge --ff-only origin/main
```

`--ff-only` 失败说明 brain worktree 状态异常（不应有提交），告知用户但不自动处理。

## 输出格式

每个分支处理后给一段简短报告：

```
[<branch>] 状态：已同步 / 远程领先 N / 本地领先 N / 分叉(N+M)
- 操作：<无 / ff-merge / merge + 处理冲突 / 重置 / 移交 PR 流程>
- 结果：<一句话>
```

总结：

```
## sync-obsidian-brain 总结
- openclaw/data: <一行>
- openclaw/config: <一行>
- brain (main): ff 到最新（或：状态异常，原因 ...）
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 某 worktree 缺失 | 跳过该分支，告知用户该 worktree 不存在 |
| 当前所在 worktree 与处理目标不一致 | 严格 `cd <worktree>` 后再执行；不要靠 `git -C` 替代（防止 alias / cwd 误判）|
| 暂存包含禁止区文件 | `git reset HEAD` 取消暂存，中止本分支同步，告知用户违规文件 |
| 暂存涉及审阅区 | 询问用户是否同意 auto-commit；不同意则中止本分支 |
| Step 6 / 7 用户没明确同意 reset | 不执行；保持现状结束本分支 |
| Step 7 合并冲突涉及审阅区 / 禁止区 | 不自行解决；列冲突等用户决策 |
| Step 7 合并后发现违规文件 | 不 push；告知用户 |
| `--force-with-lease` 失败（远端有并发提交） | 暂停；告知用户远端发生过变更，重新评估状态 |
| `git fetch` 网络失败 | 重试 1 次；仍失败告知用户检查网络 / `gh auth` |

## 安全约束

- 永远不在 `main` 分支上 commit / push
- `git reset --hard` 与 `git push --force-with-lease` **每次执行**都需要用户对本次操作明确同意；规则允许并不等于免询问
- 自动 commit 仅适用于"暂存全部在自动允许区"
- 自动解决 merge 冲突仅适用于"冲突文件全部在自动允许区"
- 即使触发来源是 Ubuntu user service（无人值守），仍然在当前对话中**同步**询问用户决策；如对话不可用，停在 Step 4 输出状态报告，不做任何写操作

## 示例

**远程领先**

```
[openclaw/data]
1. cd ~/workspace/brain-edward && pwd
2. git status --porcelain → 空
3. git fetch origin main
4. rev-list --left-right --count → 0\t3
5. 远程领先 → git merge --ff-only origin/main
6. 报告：远程领先 3 个提交，已 ff-merge
```

**本地领先 + 用户选择保留**

```
[openclaw/data]
1. 校验通过，无未提交内容
2. fetch；ahead=2 behind=0 → 本地领先
3. 列 commits + diff stat 给用户
4. 用户答"保留" → 不动
5. 报告：本地领先 2 个提交，保留待提交
6.（可选）用户接着说"那帮我提 PR" → 转 obsidian-brain-pr-workflow
```

**分叉 + 自动可解冲突**

```
[openclaw/data]
1. 校验通过，无未提交内容
2. fetch；ahead=2 behind=4 → 分叉
3. 列双侧 commits 给用户；用户答"保留本地"
4. git merge origin/main → 冲突在 .wiki/index.md（自动允许区）
5. agent 解决冲突 → git add → git commit
6. git push origin openclaw/data
7. 转 obsidian-brain-pr-workflow，让 PR 流程处理 path check
```

**分叉 + 用户选择不保留**

```
[openclaw/config]
1. ahead=1 behind=2 → 分叉
2. 列差异；用户答"不保留"
3. agent 展示 reset 命令，再次确认；用户"OK"
4. git reset --hard origin/main
5. git push --force-with-lease origin openclaw/config
6. 报告：本地与远程均已重置到 origin/main
```
