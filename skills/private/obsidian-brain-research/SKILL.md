---
name: obsidian-brain-research
description: >
  在 `~/workspace/brain` / `main` 以纯只读模式调研 Obsidian 知识库。
  用于搜索、读取、引用或总结 `.wiki/`、`atari/`、`edward/` 中已有内容，
  且本次请求不修改文件。内容写入用 `obsidian-brain-write`，Obsidian 配置修改用
  `obsidian-brain-config`，分支同步用 `sync-obsidian-brain`。
metadata:
  openclaw:
    emoji: "📖"
    requires:
      bins: ["git", "rg"]
    os: ["darwin", "linux"]
---

# obsidian-brain-research

封装 `~/workspace/brain`（main 分支）的**纯只读**调研规则。所有需要从 Obsidian 知识库读取信息但不做任何修改的场景都走这里。

## 何时使用

- 查阅 `.wiki/`、`atari/`、`edward/` 中已有的笔记和内容
- 搜索某个关键词或主题在知识库中的出现位置
- 了解知识库目录结构、归属关系、上下文
- 为后续写入或配置任务收集背景资料

不适用的场景：

- 任何写操作（创建 / 修改 / 删除文件）→ 改用 `obsidian-brain-write` 或 `obsidian-brain-config`
- 与远程 main 同步 → 改用 `sync-obsidian-brain`

## 前置条件

- worktree 已存在：`~/workspace/brain`，分支 `main`
- 系统 PATH 中可用：`git`、`rg`（或退化使用 `grep -R`）

## 工作路径与边界

| 项 | 值 |
|----|----|
| 路径 | `~/workspace/brain` |
| 分支 | `main` |
| 写权限 | **无**（绝对只读） |

## 本地策略引用

- worktree、目录归属与隐私边界以 workspace `TOOLS.md` 为权威。
- 本 skill 只在 `~/workspace/brain` 的 `main` 分支读取。
- `.wiki/`、`atari/`、`edward/` 可作为搜索 / 阅读范围；任何写入、暂存、合并或分支操作都不属于本 skill。

## 工作流

### Step 1: 切换到 brain worktree 并校验

```bash
cd ~/workspace/brain
pwd
git rev-parse --abbrev-ref HEAD
git worktree list
```

校验点（任一不满足则中止并告知用户）：

- `pwd` 输出以 `brain` 结尾且不是 `brain-edward` / `brain-config`
- 当前分支为 `main`

> 进错 worktree 是写操作误伤的最大风险源；先校验，再读。

### Step 2: 调研

按用途选择最小化命令：

**查目录结构**：

```bash
ls -la
ls -la .wiki/ atari/ edward/
```

**全文搜索关键词**（推荐 `rg`）：

```bash
rg -n --no-heading "<keyword>" .wiki/ atari/ edward/
```

如未安装 `rg`，退化为：

```bash
grep -RIn --color=never "<keyword>" .wiki/ atari/ edward/
```

**读取具体文件**：使用 Read 工具读取相对 `~/workspace/brain` 的文件路径。优先精读单个文件，避免把整片目录原文倾倒到对话中。

**列出最近变更**（仅作背景了解，不据此推断当前状态）：

```bash
git log --oneline -n 20 -- .wiki/ atari/ edward/
```

### Step 3: 输出

向用户回复时：

- 总结找到的内容，引用关键路径与节选；不要把大段笔记原文一次性贴出
- 涉及多个文件时，使用 `path:line` 形式让用户可以直接定位
- 明确说明本次仅做了只读调研，没有修改任何内容

## 输出格式

```
## 调研结论
- 关键发现 1（引用 path:line）
- 关键发现 2（引用 path:line）

## 来源
- ~/workspace/brain/<相对路径>:<行号>
- ~/workspace/brain/<相对路径>:<行号>

## 备注（如有）
- 发现的疑问 / 缺口 / 后续可写入的方向
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 当前 worktree 不是 `~/workspace/brain` | 中止；告知用户应先 `cd ~/workspace/brain`，不在错误 worktree 中执行任何命令 |
| 当前分支不是 `main` | 中止；告知用户该 worktree 状态异常，建议先运行 `sync-obsidian-brain` |
| `~/workspace/brain` 不存在 | 中止；告知用户需先创建该 worktree |
| 关键词未命中 | 明确返回"未找到"；不要编造路径或内容 |
| 用户请求修改文件 | 拒绝在本 skill 中执行；建议改用 `obsidian-brain-write` 或 `obsidian-brain-config` |

## 安全约束

- **绝对禁止**在 `~/workspace/brain` 中执行任何写操作（`>>`、`tee`、`mv`、`rm`、`git add`、`git commit`、`git checkout -B`、`git merge`、编辑文件等都不行）
- 不向群聊或子 agent 暴露 MEMORY.md 或 atari/ 中可能涉及私人信息的内容
- 调研结果回到主对话；不在子 agent 中做长文件落盘

## 示例

**用户**："查一下 .wiki 里有没有关于 daily-log 的笔记"

```
1. cd ~/workspace/brain && git rev-parse --abbrev-ref HEAD  # 应返回 main
2. rg -n --no-heading "daily.?log" .wiki/
3. 读取命中的具体文件，节选关键段落
4. 回复：列出命中文件、关键行号与一句话摘要
```

**用户**："edward 里我之前让你整理的那篇 React Server Components 总结在哪？"

```
1. cd ~/workspace/brain && git rev-parse --abbrev-ref HEAD  # 应返回 main
2. rg -n --no-heading "Server Components|RSC" edward/
3. 找到候选后用 Read 读取并给出文件路径与摘要
```
