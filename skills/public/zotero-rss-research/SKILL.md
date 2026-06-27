---
name: zotero-rss-research
description: >
  使用 zotero-cli 初始化或运行 Zotero RSS 研究流水线：读取 Zotero RSS feeds，
  将选中的条目归档到配置好的 collection，按平台规则下载 PDF，
  分析论文，并生成研究汇总。
  适用于 Zotero RSS research setup、cron runs、reruns 和添加平台 PDF 下载规则。
metadata:
  openclaw:
    emoji: "📚"
    requires:
      bins: ["zotero-cli", "python3", "node", "markitdown"]
    files:
      - "references/*"
      - "references/pdf-download/*"
      - "references/pdf-download/rules/*"
      - "scripts/*"
      - "state/*"
    os: ["linux"]
---

# zotero-rss-research

使用 `zotero-cli` 执行所有 Zotero 读写操作。PDF 下载按平台规则执行；规则可指定
http-client、browser-open、browser-click 或 manual-required。

## 全局不变量

- `state/runs/{output}` 只保存轻量状态；PDF、Markdown 和报告写入研究产物目录。
- PDF 下载后必须用 MarkItDown 转成同目录 Markdown，研究优先基于 Markdown。
- DOI 去重以 Zotero collection 为事实来源：使用 `zotero-cli items find-doi <DOI> --collection <collectionKey>`。
- Cron 不直接修改 `references/pdf-download/rules-execution.md` 或 `references/pdf-download/rules/*.md`；未知来源只写规则候选到本次 RUN。
- Cron 交付前必须通过最终门禁；缺报告或报告不完整时回复失败摘要，不宣告完成。

## 文件

- 配置：`state/config.json`
- 运行状态：`state/runs/{output}/process-items.json`
- 路径规则：`references/path-rules.md`
- Cron 主流程：`references/cron-run.md`
- 初始化/更新：`references/init-update.md`
- PDF 下载规则索引与执行门禁：`references/pdf-download/rules-execution.md`
- PDF 下载规则创建流程：`references/pdf-download/rules-create.md`
- PDF 下载规则模板：`references/pdf-download/rule-template.md`
- PDF 下载规则候选模板：`references/pdf-download/rule-candidate-template.md`
- 平台 PDF 下载规则：`references/pdf-download/rules/*.md`
- 研究 workflow 索引：`references/research-workflow.md`
- 单篇研究 workflow：`references/single-paper-workflow.md`
- 汇总研究 workflow：`references/summary-workflow.md`
- 单篇报告模板：`references/research-item-report-template.md`
- 汇总报告模板：`references/report-template.md`

## 脚本

脚本执行前先进入 `scripts/` 目录。

`collect_feed_items.py`：

- 参数：
  - `feed_ids`：JSON list，例如 `["2"]`。
  - `date`：YYYY、YYYY-MM、YYYY-MM-DD 或 YYYY-MM-DD..YYYY-MM-DD。
  - `output`：相对于 `state/runs` 的运行目录名。
- 输出：`state/runs/{output}/process-items.json`，每个 DOI 初始化为 `status=new`。
- 示例：

```bash
python3 collect_feed_items.py '["2"]' 2026-06-16..2026-06-22 2026-06-23
```

## 分支

- 用户要求初始化或更新配置：读取并执行 `references/init-update.md`。
- 用户要求 cron run、rerun、每日/每周文献分析：读取并执行 `references/cron-run.md`。
- 用户要求添加、创建或更新 PDF 下载规则：读取并执行 `references/pdf-download/rules-create.md`。
- 需要启动单篇 research agent：把 `references/single-paper-workflow.md` 的相关要求传给 research agent。
- 需要启动汇总 research agent：把 `references/summary-workflow.md` 的相关要求传给 research agent。
