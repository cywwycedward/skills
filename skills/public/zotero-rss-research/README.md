# zotero-rss-research

`zotero-rss-research` 是一个面向 Zotero RSS 文献跟踪的研究流水线 skill。它帮助 Codex 从 Zotero RSS feed 中收集新论文，下载 PDF，转换为 Markdown，归档到指定 Zotero collection，并生成单篇论文报告和本次运行的汇总报告。

它适合用于每日、每周或指定日期范围的文献追踪，尤其适合希望把 RSS 新论文自动整理成可阅读研究报告的场景。

## 主要功能

- 初始化 Zotero RSS 研究配置：选择 Zotero collection、RSS feed、报告语言、下载目录和回补窗口。
- 收集 RSS 条目：按日期或日期范围读取 Zotero feed，并按 DOI 生成本次运行清单。
- Zotero 去重：以目标 collection 为准，跳过已经入库的 DOI，避免重复下载和研究。
- PDF 下载：按平台规则自动下载全文 PDF；遇到登录、验证码或权限问题时标记为需要人工处理。
- Markdown 转换：下载 PDF 后用 MarkItDown 转成 Markdown，后续研究优先基于 Markdown。
- Zotero 归档：将新论文和 PDF 附件归档到配置好的 collection。
- 单篇论文研究：为每篇成功归档的论文生成结构化 `report.md`。
- 汇总研究报告：按主题归纳本次论文，保留成功、失败、需人工处理和已跳过条目。
- PDF 下载规则扩展：可为新出版平台创建候选规则，确认后再加入正式规则。

## 使用前准备

运行该 skill 前，本机需要具备：

- `zotero-cli`：用于读取 Zotero RSS、查询 collection、添加 DOI 和附件。
- `python3`：用于运行 RSS 条目收集脚本。
- `markitdown`：用于把 PDF 转成 Markdown。
- `node`：供相关浏览器或自动化工具使用。
- 可用的 Zotero 配置，以及目标 RSS feed。

如果要自动下载受限全文，还需要浏览器中具备相应平台的访问权限。例如 CNKI 规则依赖有效的机构订阅会话。

## 使用方法

### 1. 初始化配置

第一次使用时，让 Codex 使用该 skill 初始化：

```text
使用 zotero-rss-research 初始化 Zotero RSS 研究配置。
```

初始化过程会确认：

- 目标 Zotero collection。
- 要跟踪的 RSS feed。
- 报告语言，默认 `zh-CN`。
- PDF 下载目录。
- 回补窗口 `lookbackDays`，默认 7 天。

配置会写入本地的 `state/config.json`。该文件包含个人配置，不会提交到仓库。

### 2. 运行文献研究

可以按日、按周或指定日期范围运行：

```text
使用 zotero-rss-research 跑今天的 RSS 文献研究。
```

```text
使用 zotero-rss-research 分析 2026-06-16 到 2026-06-22 的 RSS 文献。
```

运行完成后，Codex 会返回汇总报告路径。每篇论文也会在自己的目录下生成单篇 `report.md`。

### 3. 重新运行或补跑

如果上次运行中有下载失败、人工处理或报告缺失，可以要求 rerun：

```text
重新运行 zotero-rss-research 的 2026-06-23 任务，并重试失败项。
```

Rerun 会优先复用已经存在且通过校验的 PDF，不会无意义重复下载。

### 4. 添加新的 PDF 下载规则

当遇到未覆盖的出版平台时，可以让 Codex 起草规则：

```text
为 zotero-rss-research 添加 example.com 的 PDF 下载规则，landing URL 是 ...
```

Cron 运行中发现的新平台不会直接修改正式规则，只会把候选规则写入本次运行目录。正式写入规则前，需要用户确认。

## 目录结构

```text
zotero-rss-research/
|-- SKILL.md
|-- README.md
|-- scripts/
|   `-- collect_feed_items.py
|-- references/
|   |-- init-update.md
|   |-- cron-run.md
|   |-- path-rules.md
|   |-- research-workflow.md
|   |-- single-paper-workflow.md
|   |-- summary-workflow.md
|   |-- research-item-report-template.md
|   |-- report-template.md
|   `-- pdf-download/
|       |-- rules-execution.md
|       |-- rules-create.md
|       |-- rule-template.md
|       |-- rule-candidate-template.md
|       `-- rules/
|           |-- cnki.md
|           |-- link-springer.md
|           |-- sciencedirect.md
|           |-- tandfonline.md
|           `-- wiley.md
`-- state/
    `-- runs/
```

### 关键文件说明

- `SKILL.md`：skill 入口，说明触发场景、全局规则和不同任务应读取哪些 workflow。
- `scripts/collect_feed_items.py`：从 Zotero RSS feed 中收集指定日期范围内的条目，并生成本次运行状态。
- `references/init-update.md`：初始化和更新配置的流程。
- `references/cron-run.md`：每日、每周、rerun 等完整运行流程。
- `references/path-rules.md`：状态目录、研究产物目录、PDF、Markdown 和报告的命名规则。
- `references/research-workflow.md`：单篇研究和汇总研究的共同原则。
- `references/single-paper-workflow.md`：单篇论文报告的生成要求和完成检查。
- `references/summary-workflow.md`：汇总报告的生成要求和完成检查。
- `references/research-item-report-template.md`：单篇论文报告模板。
- `references/report-template.md`：汇总报告模板。
- `references/pdf-download/rules-execution.md`：PDF 下载规则索引、平台选择流程和 PDF 校验标准。
- `references/pdf-download/rules-create.md`：新增或优化平台下载规则的流程。
- `references/pdf-download/rules/*.md`：已支持平台的 PDF 下载规则。
- `state/runs/`：保存每次运行的轻量状态，例如 `process-items.json`。

## 已内置的 PDF 平台规则

当前正式规则覆盖：

- Taylor & Francis：`www.tandfonline.com`
- Springer Nature Link：`link.springer.com`
- Elsevier ScienceDirect：`www.sciencedirect.com`
- Wiley Online Library：`onlinelibrary.wiley.com`
- 中国知网（CNKI）：`kns.cnki.net` / `www.cnki.net`

这些规则只负责可稳定自动化的下载路径。遇到登录、机构权限、验证码、付费墙或会话失效时，条目会被标记为 `needsManual`，并进入汇总报告的人工处理列表。

## 输出内容

一次完整运行通常会产生：

- `state/runs/{output}/process-items.json`：本次运行的 DOI 状态清单。
- 每篇论文的 PDF 文件。
- 每篇论文的 Markdown 文件。
- 每篇论文的单篇 `report.md`。
- 本次运行的汇总 `report.md`。
- 如发现新平台，可能生成 `pdf-download-rule-candidates.md`。

单篇报告会记录论文基本信息、研究问题、方法、关键发现、证据位置、局限、复现性和建议动作。汇总报告会归纳主题、列出支撑 DOI、说明分歧与不确定性，并保留失败、需人工处理和已在 collection 中的条目。

## 状态说明

- `studied`：已完成单篇研究，并通过报告检查。
- `skippedAlreadyInCollection`：该 DOI 已在目标 Zotero collection 中，已跳过。
- `failed`：在去重、下载、转换、归档或研究阶段失败。
- `needsManual`：需要登录、权限、验证码或其他人工介入。

只有所有条目进入终态后，skill 才会生成最终汇总报告。

## 注意事项

- 该 skill 以 DOI 为核心处理单位；没有 DOI 的 RSS 条目会被跳过。
- PDF、Markdown 和报告写入研究产物目录，`state/runs/` 只保存轻量状态。
- 研究分析优先使用 Markdown，PDF 主要作为备用证据来源。
- 自动化下载不能绕过出版平台权限限制；受限内容需要用户提供合法访问会话。
- Cron 运行不会直接更新正式 PDF 下载规则，未知平台只会生成候选规则。
