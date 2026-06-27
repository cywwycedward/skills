---
name: obsidian-brain-config
description: >
  在 `~/workspace/brain-config` / `openclaw/config` 修改 Obsidian 应用配置、
  插件配置或 TaskNotes 视图。用于 `.obsidian/` 与 `TaskNotes/` 的本次审阅后修改；
  本地改完后移交 `obsidian-brain-pr-workflow`。内容写入用 `obsidian-brain-write`，
  只读查阅用 `obsidian-brain-research`，分支同步用 `sync-obsidian-brain`。
metadata:
  openclaw:
    emoji: "⚙️"
    requires:
      bins: ["git", "gh"]
    os: ["darwin", "linux"]
---

# obsidian-brain-config

封装 `~/workspace/brain-config`（`openclaw/config` 分支）的配置修改规则。所有针对 Obsidian 应用配置（`.obsidian/`）和任务笔记插件视图（`TaskNotes/`）的修改都走这里。

## 何时使用

- 调整 Obsidian 应用配置（主题、快捷键、外观、核心插件开关）
- 修改第三方插件配置（位于 `.obsidian/plugins/`）
- 修改任务笔记插件视图配置（`TaskNotes/`）

不适用的场景：

- 写入 `edward/` / `.wiki/` / `atari/` 等内容文件 → 改用 `obsidian-brain-write`
- 只读查阅 → 改用 `obsidian-brain-research`
- 与远程 main 同步 → 改用 `sync-obsidian-brain`

## 前置条件

- worktree 已存在：`~/workspace/brain-config`，分支 `openclaw/config`
- 系统 PATH 中可用：`git`、`gh`
- `gh auth status` 处于已登录状态

## 本地策略引用

- worktree / 权限 / PR 策略以 workspace `TOOLS.md` 为权威。
- 本 skill 只在 `~/workspace/brain-config` 的 `openclaw/config` 分支执行。
- 局部 gate：`brain-config` 没有自动允许区；`.obsidian/` 与 `TaskNotes/` 都必须先获用户对本次具体内容的审阅同意；其他路径立即中止。

## 工作流

### Step 1: 切换到 brain-config 并校验

```bash
cd ~/workspace/brain-config
pwd
git rev-parse --abbrev-ref HEAD
git status --porcelain
```

校验点（任一不满足则中止并告知用户）：

- `pwd` 末尾是 `brain-config`（不是 `brain` 也不是 `brain-edward`）
- 当前分支为 `openclaw/config`

> Obsidian 配置文件（尤其 `.obsidian/workspace.json`、`.obsidian/appearance.json`）会被 Obsidian 应用本身频繁改写。**确认是不是 Obsidian 自己写的**，再决定是不是要 stash / 丢弃 / 一并提交。

如果 `git status --porcelain` 显示有非本次任务的残留改动，先告知用户、问清来源（多半是 Obsidian 进程在跑），由用户决定保留、stash、还是与本次修改一并提交。**不要自动覆盖未知改动。**

### Step 2: 同步基线（推荐）

```bash
git fetch origin main
if ! git merge --ff-only origin/main; then
  git status --porcelain
  git log --oneline --left-right HEAD...origin/main -n 20
  echo "ff-only merge failed; run sync-obsidian-brain before continuing" >&2
  exit 1
fi
```

`--ff-only` 失败说明有领先提交或分叉，不在本 skill 内处理；提示用户先运行 `sync-obsidian-brain`。

### Step 3: 审阅模式（必经）

无论改 `.obsidian/` 还是 `TaskNotes/`，都按审阅模式执行：

1. 先把**完整修改计划**列给用户：
   - 要改哪个文件（具体路径）
   - 为什么改（用户原始诉求映射到具体配置项）
   - 改成什么样（值的前后对比、JSON 字段差异）
   - 副作用（是否影响其他视图、是否需要重启 Obsidian、是否可能与已开启的插件冲突）
2. 等用户**对本次内容明确同意**后再进入 Step 4
3. 涉及非显而易见路径变更（启用 / 禁用插件、删除整段配置）时，建议同时给出回滚方法

> 不能拿过去某次"你可以改 .obsidian/" 的泛许可来跳过本步。

### Step 4: 执行修改

- 使用 Edit / Write 工具修改文件
- JSON 配置：保持文件原本格式（缩进风格、键顺序），仅做必要的最小改动
- 删除文件优先使用 trash，不使用 `rm`
- 一次任务的修改集中提交一次

### Step 5: 提交前自检

```bash
git status --porcelain
git diff --stat
git diff
```

逐项检查：

- [ ] 所有变更路径都在 `.obsidian/` 或 `TaskNotes/` 内
- [ ] 没有意外修改 `edward/`、`.wiki/`、`atari/`、`.github/`
- [ ] JSON 文件结构合法（必要时 `python -m json.tool < file.json` 或 `jq . < file.json` 校验）
- [ ] diff 内容与用户审阅的计划一致

发现意外文件 → `git restore <path>` 还原。JSON 解析失败必须在提交前修好，否则会污染分支。

### Step 6: 移交 PR 流程

调用 `obsidian-brain-pr-workflow`，传入参数：

- `worktree_path`: `~/workspace/brain-config`
- `branch`: `openclaw/config`

PR 流程会处理 commit / push / PR 创建 / path check / 等待用户审核。`obsidian-brain-config` 的所有修改都属于审阅区，PR 走的是"等用户审核"分支，**不会自动 merge**。

## 中止写入

| 状态 | 处理 |
|------|------|
| **未 commit** | `git restore .` 还原已修改文件；`git clean -fd`（先 `-n` 预览）清理未跟踪文件 |
| **已 commit 未 push** | `git reset --soft HEAD~1` 撤销 commit，文件改动保留；如确认全部丢弃，`git reset --hard HEAD~1`（询问用户后执行）|

> push 之后无法用上述方法回滚。此时走 `obsidian-brain-pr-postreview` 的 closed 流程（reset 本地 + 远程到 main）。

## 输出格式

```
## 已修改文件
- <path1>: <字段 / 行数 / 一句话说明>
- <path2>: <字段 / 行数 / 一句话说明>

## 审阅状态
- 用户已对本次修改内容明确同意（同意点：<引用用户原话或要点>）

## 副作用提示
- 是否需要重启 Obsidian / 重新加载插件 / 可能与某插件冲突

## 下一步
- 已移交 obsidian-brain-pr-workflow；该 PR 属审阅区，将等待你在 GitHub 上 review & merge
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 当前 worktree 不是 brain-config | 中止；提示用户先 `cd ~/workspace/brain-config` |
| 当前分支不是 `openclaw/config` | 中止；提示该 worktree 状态异常，建议先 `sync-obsidian-brain` |
| 工作区有未知改动（很可能是 Obsidian 进程自行写入） | 暂停；告知用户具体文件清单，问清来源后再处理 |
| 用户要求改 `edward/` / `.wiki/` / `atari/` | 拒绝；建议切到 `obsidian-brain-write` |
| 用户要求改未列出的目录 | 拒绝；说明仅支持 `.obsidian/`、`TaskNotes/` |
| 用户口头让你改但没给具体计划 | 在 Step 3 主动列出修改计划等用户确认 |
| JSON 修改后解析失败 | 提交前必须修好；不要带着坏配置 push |
| `--ff-only` 同步 origin/main 失败 | 暂停；建议先运行 `sync-obsidian-brain` |

## 安全约束

- 写操作前**必须**确认 `pwd` 末尾是 `brain-config` 且分支是 `openclaw/config`
- `.obsidian/` 和 `TaskNotes/` 的所有修改都必须先经用户对**本次具体内容**审阅同意
- 不在 push 前 `git push --force`
- 不擅自启用 / 禁用第三方插件（属高副作用变更，必须在审阅计划中显式列出）
- 删除文件优先使用 trash
- 不在子 agent 内执行写操作

## 示例

**用户**："把 obsidian 的字号调大一点"

```
1. cd ~/workspace/brain-config → 校验分支 openclaw/config
2. git fetch origin main && git merge --ff-only origin/main
3. 审阅模式：
   - 列出 .obsidian/appearance.json 中的 baseFontSize 当前值
   - 提议改成多少（给一个具体数值）
   - 副作用：仅本机 Obsidian 字号变大，需重启 Obsidian 生效
   - 等用户确认
4. 用户同意 → Edit .obsidian/appearance.json
5. JSON 校验 → git diff 自检
6. 调用 obsidian-brain-pr-workflow（worktree=brain-config, branch=openclaw/config）
```

**用户**："给 TaskNotes 加一个'本周到期'视图"

```
1. cd ~/workspace/brain-config → 校验分支 openclaw/config
2. 审阅模式：
   - 找到 TaskNotes/views/ 下现有视图配置作为模板
   - 列出新视图的 JSON 结构（name、filter 表达式等）
   - 副作用：Obsidian 重新加载 TaskNotes 后视图列表新增一项
   - 等用户确认
3. 用户同意 → Write 新视图文件
4. 自检 → 调用 obsidian-brain-pr-workflow
```
