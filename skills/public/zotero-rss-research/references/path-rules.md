# Zotero RSS 路径规则

每次运行同时使用一个轻量状态目录和一个研究产物目录。

## 状态目录

- 状态目录：`state/runs/{output}`。
- 只保存 `process-items.json` 等轻量运行状态。
- 不要把 PDF、Markdown 转换结果或研究报告写入状态目录。

## 研究产物目录

- 研究 ROOT：由 CRON 指定；如果 CRON 未指定，使用
  `/home/cywwycatari/workspace/brain-edward/edward/cron/{cron_name}`。
- 研究 RUN：`{ROOT}/{output}`，例如
  `/home/cywwycatari/workspace/brain-edward/edward/cron/daily_paper_research/2026-06-14`。
- 单篇论文目录：`{RUN}/{sanitized_title}_{sanitized_doi}`。
- PDF：`{paper_dir}/{sanitized_doi}.pdf`。
- Markdown：`{paper_dir}/{sanitized_doi}.md`，由 MarkItDown 从 PDF 转换得到。
- 单篇报告：`{paper_dir}/report.md`。
- 汇总报告：先写为 `{RUN}/report.md`；研究完成后可按内容重命名为
  `{RUN}/{YYYY-MM-DD}_{research_theme}.md`。
- PDF 下载规则候选：`{RUN}/pdf-download-rule-candidates.md`，只在本次运行发现新平台规则时创建。

## 命名规则

- `sanitized_title`：保留标题主要词语，将空格和路径非法字符替换为 `_`。
- `sanitized_doi`：将 DOI 中的 `/`、空格和路径非法字符替换为 `_`。

## process-items 字段

下载和转换完成后，`process-items.json` 中每个 DOI 条目必须包含：

```json
{
  "title": "Paper title",
  "url": "https://publisher.example/article",
  "filePath": "/abs/path/to/10.1234_example.pdf",
  "markdownPath": "/abs/path/to/10.1234_example.md",
  "reportPath": "",
  "downloadRulePath": "references/pdf-download/rules/example.md",
  "downloadMethod": "browser-open",
  "downloadTrigger": "https://publisher.example/paper.pdf",
  "downloadOriginalFilename": "paper.pdf",
  "status": "new",
  "zoteroItemKey": "",
  "skipReason": "",
  "failureStage": "",
  "lastError": ""
}
```

`filePath`、`markdownPath` 和 `reportPath` 必须使用研究产物目录内的绝对路径；其中
`reportPath` 在单篇研究通过门禁前可为空字符串。`downloadRulePath`、`downloadMethod`、
`downloadTrigger` 和 `downloadOriginalFilename` 记录本次实际下载诊断信息；下载失败或需
人工处理时也尽量写入已知字段。
