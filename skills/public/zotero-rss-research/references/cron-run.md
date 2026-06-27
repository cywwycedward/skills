# Zotero RSS Cron 运行

本文件是 cron/rerun 的主流程。路径按 `references/path-rules.md` 执行。

## 前置检查

1. 读取 `state/config.json`。如果缺少配置，停止并回复用户先初始化。
2. 确认工具可用：

   ```bash
   zotero-cli --version
   zotero-cli config validate
   markitdown --version
   ```

3. 读取 `references/path-rules.md`、`references/pdf-download/rules-execution.md`、报告模板和研究 workflow。
4. 单篇研究使用 `references/single-paper-workflow.md`；汇总研究使用
   `references/summary-workflow.md`。`references/research-workflow.md` 只作索引。

## 1. 收集 RSS 条目

1. 从 cron 描述确定目标日期 `targetDate`。
   - 每日早间运行：`targetDate=昨天`。
   - 每日晚间运行：`targetDate=今天`。
   - 周运行：按 cron 描述确定日期范围。
2. 读取 `lookbackDays`，缺省为 `7`。
3. 每日运行的 `date` 参数使用回补窗口：
   - `date={targetDate - lookbackDays + 1}..{targetDate}`
   - 例如 targetDate 是 `2026-06-22` 且 `lookbackDays=7`，则 date 为
     `2026-06-16..2026-06-22`。
4. `output` 使用本次运行日期或 cron 指定的运行标识。
5. 运行收集脚本：

   ```bash
   cd /home/cywwycatari/workspace/skills/zotero-rss-research/scripts
   python3 collect_feed_items.py '["2"]' 2026-06-16..2026-06-22 2026-06-23
   ```

6. 如果 `process-items.json` 没有条目，停止并最终回复：
   - 查询日期或日期范围。
   - RSS feed。
   - 条目数为 0。
   - 无新条目，未生成报告。

## 2. Zotero collection DOI 去重

对 `process-items.json` 中每个 DOI 运行：

```bash
zotero-cli items find-doi "<DOI>" --collection "<collectionKey>"
```

判定规则：

- 如果 stdout 非空且包含 `key:`，该 DOI 已在目标 collection 中。
  - 将条目更新为：
    - `status`: `skippedAlreadyInCollection`
    - `zoteroItemKey`: stdout 中的 key
    - `skipReason`: `already in collection`
  - 不下载、不转换、不归档、不研究。
- 如果 stdout 为空，该 DOI 进入处理队列。
- 如果命令报错，将条目标记为失败：
  - `status`: `failed`
  - `failureStage`: `doi-dedupe`
  - `lastError`: 命令错误摘要。

如果所有条目都已在 collection 中，最终回复必须明确说明本次无新 DOI 需要研究，并列出跳过数量。

## 3. 下载 PDF

只处理 `status=new` 的条目。

1. 按路径规则创建每篇论文目录。
2. Rerun 时，如果 `{paper_dir}/{sanitized_doi}.pdf` 已存在且通过
   `references/pdf-download/rules-execution.md` 的 PDF 文件门禁，直接更新为
   `status=downloaded`，不重复下载。
3. 读取 `references/pdf-download/rules-execution.md`，根据 landing URL 或 DOI landing page 的
   domain 选择一个平台规则文档。
4. 只加载匹配的平台规则文档，并按文档中的下载方式触发 PDF 下载。
   - `browser-open`：按规则推导 PDF URL，用浏览器打开并从配置下载目录定位文件。
   - `browser-click`：用浏览器打开页面，并执行规则中写明的下载或点击命令。
   - `http-client`：执行规则中写明的 `curl` 或 `wget` 命令。
   - `manual-required`：标记为 `needsManual`，不继续自动下载。
5. 按 `references/pdf-download/rules-execution.md` 校验下载结果。
6. 下载完成后，把 PDF 移动到：

   ```text
   {paper_dir}/{sanitized_doi}.pdf
   ```

7. 更新条目：
   - `filePath`: PDF 绝对路径。
   - `downloadRulePath`: 使用的平台规则文档路径。
   - `downloadMethod`: `browser-open`、`browser-click` 或 `http-client`。
   - `downloadTrigger`: 实际触发下载的 URL、按钮 ref 或命令摘要。
   - `downloadOriginalFilename`: 下载事件或目录观察得到的原始文件名。
   - `status`: `downloaded`。

### 未知 PDF 规则

如果 `references/pdf-download/rules-execution.md` 中没有适用规则：

1. 使用 browser 探索 landing page。
2. 如果找到 PDF URL 或按钮路径，只用于本次下载。
3. 不要在 cron 中修改 `references/pdf-download/rules-execution.md` 或平台规则文件。
4. 按 `references/pdf-download/rule-candidate-template.md` 将候选规则追加写入
   `{RUN}/pdf-download-rule-candidates.md`。

如果发生技术失败，将条目标记为失败：

- `status`: `failed`
- `failureStage`: `download`
- `lastError`: 失败原因。

如果需要登录、机构权限、验证码或其他人工介入，将条目标记为：

- `status`: `needsManual`
- `failureStage`: `download`
- `lastError`: 需要人工处理的原因。

Rerun 时，除非用户明确要求重试，跳过 `needsManual` 条目，并在汇总报告中列出。

## 4. 转换 PDF 为 Markdown

只处理 `status=downloaded` 的条目。

对每篇 PDF 运行：

```bash
markitdown "{paper_dir}/{sanitized_doi}.pdf" -o "{paper_dir}/{sanitized_doi}.md"
```

转换门禁：

- Markdown 文件存在。
- Markdown 文件非空。
- Markdown 正文包含 DOI 或标题关键词。

门禁通过后更新条目：

- `markdownPath`: Markdown 绝对路径。
- `status`: `converted`。

门禁失败时更新条目：

- `status`: `failed`
- `failureStage`: `markitdown`
- `lastError`: 转换失败原因或校验失败原因。

不要把 PDF 原文、base64、完整 browser snapshot 或整份大 Markdown 直接塞进主模型上下文。

## 5. Zotero 归档

只处理 `status=converted` 的条目。

使用：

```bash
zotero-cli items add-doi "<DOI>" --attach "<PDF filePath>" --collection "<collectionKey>" --attach-title "Full Text PDF"
```

成功后更新条目：

- `status`: `archived`
- `zoteroItemKey`: 返回或可查到的 item key。

失败后更新条目：

- `status`: `failed`
- `failureStage`: `zotero-archive`
- `lastError`: 错误摘要。

## 6. 单篇研究

只处理 `status=archived` 的条目。

1. 调用 `agents_list` 确认可用 `research` agent。
2. 所有 `sessions_spawn` 必须带 `agentId: "research"`。
3. 每个 subagent 负责一篇论文，任务必须包含：
   - DOI
   - 标题
   - 原始 URL
   - PDF 绝对路径
   - Markdown 绝对路径
   - 单篇输出目录绝对路径
   - 预期 `report.md` 绝对路径
   - 报告语言
   - `references/single-paper-workflow.md` 的完成门禁
4. research agent 必须优先阅读 Markdown；PDF 只作为备用文件路径，不要整份读入上下文。
5. 如果 Markdown 过大，按 `references/single-paper-workflow.md` 的证据抽取流程处理。
6. 每个 subagent 完成后，主 agent 立即检查：
   - `report.md` 存在。
   - 文件非空。
   - 正文包含 DOI。
   - 正文包含论文类型。
   - 至少有 1 条带证据位置的关键发现。
   - 如果论文属于经验研究，报告中至少满足以下之一：
     - 包含至少 1 个关键指标或数值结果。
     - 明确写出“当前证据下无法可靠提取关键数值”。
7. 检查通过后更新：
   - `status`: `studied`
   - `reportPath`: 单篇报告绝对路径

### 步骤 6 完成门禁

所有 subagent 返回（或 `sessions_yield` 恢复）后，主 agent 必须执行本门禁。
逐条目确认报告已落盘且 `process-items.json` 状态已更新。不管是否使用
`sessions_yield`，本门禁不可跳过。

1. 重新读取 `process-items.json`。
2. 对每个 `status=archived` 的条目，根据 `markdownPath` 所在目录推导
   `{paper_dir}/report.md`。
3. 对每个预期报告执行检查：
   - 文件存在。
   - 文件大小大于 0。
   - 正文包含该条目的 DOI。
   - 正文包含论文类型。
   - 至少有 1 条带证据位置的关键发现。
4. 如果报告明确属于经验研究，再额外检查至少满足以下之一：
   - 包含至少 1 个关键指标或数值结果。
   - 明确写出“当前证据下无法可靠提取关键数值”。
5. 检查通过的条目立即更新 `process-items.json`：
   - `status`: `studied`
   - `reportPath`: 单篇报告绝对路径
6. subagent 返回失败、LLM 失败、超时、报告缺失、报告为空、报告不含 DOI、
   缺少论文类型、缺少关键发现，或经验研究缺少关键数值且未说明原因时，
   按该 DOI 重试 1-2 次。重试任务仍必须包含
   `references/single-paper-workflow.md` 的完成门禁。
7. 最终仍失败时更新：
   - `status`: `failed`
   - `failureStage`: `single-paper-research`
   - `lastError`: 最后错误摘要，例如缺少报告、报告为空、报告不含 DOI、缺少论文类型、缺少关键发现、经验研究缺少关键数值说明或 subagent 空结束。
8. 重读 `process-items.json`：确认 `status=archived` 的条目数为 0。
   只有当所有条目都达到终态，步骤 6 才算完成。

## 7. 汇总研究

进入步骤 7 前，必须已通过步骤 6 完成门禁（所有条目 status 为终态）。
读取 `process-items.json`，逐条目确认终态。
任何条目 status 仍为 `archived` 时，立即返回步骤 6 完成门禁流程，不继续
进入步骤 7。

终态包括：

- `studied`
- `skippedAlreadyInCollection`
- `failed`
- `needsManual`

汇总任务必须包含：

- `process-items.json` 绝对路径。
- RUN 输出目录绝对路径。
- 汇总 `report.md` 绝对路径。
- 所有成功单篇报告路径。
- DOI 到 PDF 绝对路径映射。
- DOI 到 Markdown 绝对路径映射。
- 失败条目列表。
- 需人工处理条目列表。
- 已跳过的 collection 内已有 DOI 列表。
- `{RUN}/pdf-download-rule-candidates.md` 路径；如果不存在，说明无候选规则。
- RSS feed 标识或名称；如果未知，明确说明未提供。
- 条目日期范围；如果未知，明确说明未提供。
- 本次 RUN 的总条目数；如果未知，明确说明未提供。
- 无 DOI 而被跳过的条目数；如果未知，明确说明未提供。
- 报告语言。
- `references/summary-workflow.md` 的汇总要求。

汇总报告必须使用 `references/report-template.md` 的结构，并保留：

- 成功研究论文。
- 已跳过已入库 DOI。
- 失败或需人工处理条目。
- PDF 下载规则候选；没有时写“无”。

## 8. 最终门禁

交付前，主 agent 必须检查：

1. 汇总报告文件存在且非空。
2. 汇总报告包含所有 `studied` DOI。
3. 汇总报告列出所有 `failed` DOI 及原因。
4. 汇总报告列出所有 `needsManual` DOI 及原因。
5. 汇总报告列出 `skippedAlreadyInCollection` 计数；如果有跳过条目，列出 DOI。
6. 汇总报告的“主题归纳”对每个主题列出支撑 DOI；如果无可归纳主题，明确写“无可归纳主题”。
7. 汇总报告包含“分歧与不确定性”小节。
8. 汇总报告包含“PDF 下载规则候选”小节；没有候选时写“无”。
9. `studied + failed + needsManual + skippedAlreadyInCollection` 数量等于 `process-items.json` 条目数。

门禁失败时，最终回复必须是失败摘要：

- 缺失或不合格的文件路径。
- 失败的 DOI。
- 最后错误。
- 不要宣告研究完成。

门禁通过后，发送最终汇总给用户，并提供报告路径。
