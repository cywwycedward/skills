# PDF 下载规则索引与执行门禁

本文件负责选择平台规则，并规定下载后的文件门禁、记录字段和 rerun 行为。平台规则只写平台特有的下载入口、触发动作和下载产物定位方式。

## 平台规则

| 平台 | 匹配条件 | 下载方式摘要 | 规则文档 |
| --- | --- | --- | --- |
| Taylor & Francis | `www.tandfonline.com` | browser-open：打开 epdf viewer 后在浏览器 session 中 blob fetch 下载 | `references/pdf-download/rules/tandfonline.md` |
| Springer Nature Link | `link.springer.com` | browser-open：打开 PDF URL 后在浏览器 tab 中 blob fetch 下载 | `references/pdf-download/rules/link-springer.md` |
| Elsevier ScienceDirect | `www.sciencedirect.com` | browser-open：打开 landing page 提取 pdfft URL，通过新 tab 打开后 blob fetch 下载 | `references/pdf-download/rules/sciencedirect.md` |
| Wiley Online Library | `onlinelibrary.wiley.com` | browser-open：打开 epdf viewer 后在浏览器 session 中 blob fetch 下载 | `references/pdf-download/rules/wiley.md` |
| 中国知网（CNKI） | `kns.cnki.net` / `www.cnki.net` | browser-click：搜索标题→打开文章摘要页→点击 PDF下载；需机构订阅会话 | `references/pdf-download/rules/cnki.md` |

## 选择流程

1. 从 RSS item 的 `url` 提取 domain；如果 `url` 不是出版商页面，则打开 DOI
   landing page 后用最终页面 domain。
2. 命中上表后，只读取对应的规则文档。
3. 按规则文档的下载方式触发 PDF 下载；规则可以指定 http-client、browser-open、
   browser-click 或 manual-required。
4. 未命中任何规则时，使用浏览器探索 landing page，但不要修改本文件或平台规则文件。
5. Cron 发现稳定新规则时，只写入 `{RUN}/pdf-download-rule-candidates.md`。
6. 候选规则按 `references/pdf-download/rule-candidate-template.md` 记录。

## PDF 文件门禁

只有同时满足以下条件，才能把条目标记为 `downloaded`：

- 目标 PDF 文件存在。
- 文件大小大于 0。
- 文件开头是 `%PDF-`，或 `file` 命令识别为 PDF。

门禁失败时设置：

- `status=failed`
- `failureStage=download`
- `lastError` 写明失败原因。

## 记录字段

每次下载成功、失败或需人工处理时，尽量更新：

- `downloadRulePath`
- `downloadMethod`
- `downloadTrigger`
- `downloadOriginalFilename`

`downloadOriginalFilename` 来自 browser download event、下载目录观察或平台响应文件名；无法稳定确认时写空字符串。

## Rerun

Rerun 时先检查 `{paper_dir}/{sanitized_doi}.pdf`：

- 已存在且通过 PDF 文件门禁：直接复用，设置 `status=downloaded`。
- 已存在但门禁失败：保留失败原因，不继续使用该文件。
- 条目状态为 `needsManual`：默认跳过，除非用户明确要求重试。

## 候选规则记录

未覆盖来源的候选规则写入 `{RUN}/pdf-download-rule-candidates.md`。候选内容按
`references/pdf-download/rule-candidate-template.md` 记录。
