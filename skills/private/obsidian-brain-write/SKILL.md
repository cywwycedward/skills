---
name: obsidian-brain-write
description: >
  在 `~/workspace/brain-edward` / `openclaw/data` 创建、修改、删除或持久化
  Obsidian 知识库的非配置内容。用于写入 `edward/`、`.wiki/`，或经用户本次
  审阅同意后修改 `atari/`；本地改完后移交 `obsidian-brain-pr-workflow`。
  `.obsidian/` 与 `TaskNotes/` 用 `obsidian-brain-config`，只读查阅用
  `obsidian-brain-research`，分支同步用 `sync-obsidian-brain`。
metadata:
  openclaw:
    emoji: "✍️"
    requires:
      bins: ["git", "gh"]
    os: ["darwin", "linux"]
---

# obsidian-brain-write

封装 `~/workspace/brain-edward`（`openclaw/data` 分支）的写入规则。所有 AI 在 Obsidian 知识库中持久化内容（除 Obsidian 配置外）的操作都走这里。

## 何时使用

- 更新 memory wiki（`.wiki/`）
- 保存 AI 调研 / 生成的内容到 `edward/`
- 优化或整理用户的 `atari/` 内容（**审阅后**写入）
- 任何 AI 在知识库中持久化非配置类内容的需求

不适用的场景：

- 修改 `.obsidian/` 或 `TaskNotes/` → 改用 `obsidian-brain-config`
- 只读查阅 → 改用 `obsidian-brain-research`
- 与远程 main 同步 → 改用 `sync-obsidian-brain`

## 前置条件

- worktree 已存在：`~/workspace/brain-edward`，分支 `openclaw/data`
- 系统 PATH 中可用：`git`、`gh`（gh 用于后续 PR）
- `gh auth status` 处于已登录状态

## 本地策略引用

- worktree / 权限 / PR 策略以 workspace `TOOLS.md` 为权威。
- 本 skill 只在 `~/workspace/brain-edward` 的 `openclaw/data` 分支执行。
- 局部 gate：`edward/` 与 `.wiki/` 为自动模式；`atari/` 为审阅模式；其他路径立即中止。

## 工作流

### Step 1: 切换到 brain-edward 并校验

```bash
cd ~/workspace/brain-edward
pwd
git rev-parse --abbrev-ref HEAD
git status --porcelain
```

校验点（任一不满足则中止并告知用户）：

- `pwd` 末尾是 `brain-edward`（不是 `brain` 也不是 `brain-config`）
- 当前分支为 `openclaw/data`

> **进错 worktree 是最大风险**：在 brain（main）里 commit 会污染主分支，在 brain-config 里写 edward/ 会被 path check 拒。先校验，再写。

如果 `git status --porcelain` 显示有非本次任务的残留改动，先告知用户、问清来源，再决定是保留、暂存（`git stash`）还是清理。**不要自动覆盖未知改动。**

### Step 2: 同步基线（推荐但不强制）

为减少 PR 阶段的合并冲突，建议先把 `openclaw/data` 跟上 `origin/main`：

```bash
git fetch origin main
if ! git merge --ff-only origin/main; then
  git status --porcelain
  git log --oneline --left-right HEAD...origin/main -n 20
  echo "ff-only merge failed; run sync-obsidian-brain before continuing" >&2
  exit 1
fi
```

如果 `--ff-only` 失败（说明本地有领先提交或分叉），不要在本 skill 内自行处理，提示用户考虑先运行 `sync-obsidian-brain`。

### Step 3: 按目标目录决定模式

根据修改目标判断模式：

| 目标目录 | 模式 | 操作 |
|---------|------|------|
| 仅 `edward/` 和 / 或 `.wiki/` | **自动模式** | 直接进入 Step 4 修改 |
| 涉及 `atari/` | **审阅模式** | 先向用户说明：要改哪些文件、改什么、为什么。**等用户明确同意后**再进入 Step 4 |
| 涉及其他目录 | **禁止** | 立即中止；告知用户该路径不在写入许可范围内 |

> 审阅模式的"同意"必须是用户对**本次修改的具体内容**的同意，不能拿过去某次"你可以改 atari/" 的泛许可来跳过。

### Step 4: 执行修改

- 使用 Edit / Write 工具进行文件修改
- 删除文件优先使用 trash，不使用 `rm`：
  ```bash
  command -v trash >/dev/null && trash <path> || mv <path> ~/.Trash/  # macOS
  # Linux 没有原生 trash 时，先确认能否安装 trash-cli；不行再询问用户是否使用 rm
  ```
- 一次任务的修改**集中提交一次**；避免拆成多个不相关的 commit

### Step 5: 提交前自检

```bash
git status --porcelain
git diff --stat
git diff
```

逐项检查：

- [ ] 所有变更路径都在本次任务允许的目录内（自动区或已获用户同意的审阅区）
- [ ] 没有意外修改 `.obsidian/`、`TaskNotes/`、`.github/`
- [ ] diff 内容与用户期望一致（敏感内容、错别字、临时调试痕迹）

发现意外文件 → `git restore <path>` 或 `git checkout -- <path>` 还原，再继续。

### Step 6: 移交 PR 流程

调用 `obsidian-brain-pr-workflow`，传入参数：

- `worktree_path`: `~/workspace/brain-edward`
- `branch`: `openclaw/data`

`obsidian-brain-pr-workflow` 内部会负责 `git add` / `commit` / `push` / `gh pr create` / `gh pr checks --watch` 以及后续决策。**不要在本 skill 内自行 push 或建 PR**，避免重复逻辑。

## 中止写入

用户或 agent 在 push 前决定放弃本次修改时：

| 状态 | 处理 |
|------|------|
| **未 commit** | `git restore .` 还原已修改文件；`git clean -fd` 清掉新建的未跟踪文件（先 `-n` 预览）|
| **已 commit 未 push** | `git reset --soft HEAD~1` 撤销最近一次 commit，文件改动保留供后续手动处理；如确认要全部丢弃，再用 `git reset --hard HEAD~1`（询问用户后执行）|

> push 之后无法用上述方法回滚。此时需要走 `obsidian-brain-pr-postreview` 的 closed 流程（reset 本地 + 远程到 main）。

## 输出格式

完成本 skill 后向用户回复：

```
## 已修改文件
- <path1>: <一句话说明>
- <path2>: <一句话说明>

## 模式
- 自动区 / 审阅区（已获同意）

## 下一步
- 已移交 obsidian-brain-pr-workflow，正在处理 commit / push / PR
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 当前 worktree 不是 brain-edward | 中止；提示用户先 `cd ~/workspace/brain-edward` |
| 当前分支不是 `openclaw/data` | 中止；提示该 worktree 状态异常，建议先 `sync-obsidian-brain` |
| 工作区有未知残留改动 | 中止；询问用户来源与处理方式（保留 / stash / 丢弃） |
| 用户要求改 `.obsidian/` 或 `TaskNotes/` | 拒绝；建议切到 `obsidian-brain-config` |
| 用户要求改未列出的目录（如根目录新文件） | 拒绝；说明仅支持 edward/、.wiki/、atari/ |
| `--ff-only` 同步 origin/main 失败 | 暂停写入；建议先运行 `sync-obsidian-brain` |
| 修改 `atari/` 但用户尚未对本次内容明确同意 | 暂停；先把修改计划完整列给用户审阅 |

## 安全约束

- 写操作前**必须**确认 `pwd` 末尾是 `brain-edward` 且分支是 `openclaw/data`
- 修改 `atari/` 必须先向用户说明完整修改计划并获得同意
- 不在本 skill 内执行 push；PR 流程负责普通 push，path check 修复默认使用追加 commit，不重写历史
- 删除文件优先使用 trash
- 不在子 agent 内执行写操作（子 agent 不加载完整 skill 上下文）

## 示例

**用户**："把刚才的 React Server Components 调研整理一篇笔记存到 edward/notes/"

```
1. cd ~/workspace/brain-edward → 校验分支 openclaw/data
2. git fetch origin main && git merge --ff-only origin/main（保持基线新）
3. 模式判断：仅 edward/ → 自动模式
4. Write edward/notes/react-server-components.md
5. git status / git diff 自检
6. 调用 obsidian-brain-pr-workflow（worktree=brain-edward, branch=openclaw/data）
```

**用户**："你之前帮我整理的 atari/journals/2026-05.md 里几个错别字改一下"

```
1. cd ~/workspace/brain-edward → 校验分支 openclaw/data
2. 模式判断：涉及 atari/ → 审阅模式
3. 先列出"具体在哪几行改什么"给用户，等明确同意
4. 用户同意 → Edit 修改
5. 自检 → 调用 obsidian-brain-pr-workflow
```

## TIPS：Memory-wiki 写入规则

- 创建/刷新 synthesis 用 `openclaw wiki apply synthesis`
- synthesis 必须带 `--source-id`
- dream report 只作为线索；事实结论优先回链 daily note source
- 写入或 apply 后运行 `openclaw wiki compile`
- 重要整理后运行 `openclaw wiki lint`
- 变更在 `brain-edward/.wiki`，按 obsidian-brain-pr-workflow 提交
