# Zotero RSS 研究汇总报告模板

> 使用方式：研究完成后，将占位符替换为本次运行的真实信息；删除未使用的小节。一个报告可以包含 0 个、1 个或多个主题。

## 基本信息

- 运行日期：`{{run_date}}`
- 条目日期范围：`{{item_date_range}}`
- RSS feeds：`{{feed_ids_or_names}}`
- Zotero collection：`{{collection_name}}`
- 报告性质：`{{report_type}}`
- 总 RSS 条目数：`{{total_item_count}}`
- 无 DOI 跳过数：`{{skipped_without_doi_count_or_not_provided}}`
- 已研究论文数：`{{studied_count}}`
- 失败论文数：`{{failed_count}}`
- 需人工处理论文数：`{{needs_manual_count}}`
- 已跳过已入库论文数：`{{already_in_collection_count}}`
- 报告语言：`{{report_language}}`

## 总览

用 3-6 句话概括本次 RSS 条目的主要研究方向、共同问题、关键结论和整体价值。

- 本次最强结论：`{{strongest_takeaway}}`
- 本次最大不确定性：`{{largest_uncertainty}}`

## 语料边界与偏差

- 纳入范围：`{{inclusion_scope}}`
- 排除范围：`{{exclusion_scope}}`
- DOI、下载、转换或权限带来的样本缺口：`{{coverage_gaps}}`
- 对解读边界的说明：`{{interpretation_boundary}}`

## 主题归纳

> 按需要重复 0-N 个主题。一个主题至少由 2 篇已研究论文支撑；只有 1 篇支撑的内容放入“单篇值得关注的观察”。

### 主题一：`{{theme_name}}`

- 支持 DOI：`{{supporting_dois}}`
- 代表论文：`{{paper_titles_or_indexes}}`
- 核心问题：`{{shared_research_question}}`
- 主要结论：`{{main_findings}}`
- 证据强度：`{{evidence_strength}}`
- 反例或冲突 DOI：`{{conflicting_dois_or_none}}`
- 仍待验证的问题：`{{open_questions}}`
- 建议动作：`{{theme_action}}`

### 主题二：`{{theme_name}}`

- 支持 DOI：`{{supporting_dois}}`
- 代表论文：`{{paper_titles_or_indexes}}`
- 核心问题：`{{shared_research_question}}`
- 主要结论：`{{main_findings}}`
- 证据强度：`{{evidence_strength}}`
- 反例或冲突 DOI：`{{conflicting_dois_or_none}}`
- 仍待验证的问题：`{{open_questions}}`
- 建议动作：`{{theme_action}}`

### 单篇值得关注的观察

- 论文：`{{paper_title}}`
- DOI：`{{doi}}`
- 值得关注的原因：`{{why_noteworthy}}`
- 后续动作：`{{follow_up_action}}`

## 论文速览

| 序号 | 论文 | DOI | 论文类型 | 方法/数据 | 关键结果 | 证据强度 | 相关性 | 阅读优先级 | 建议动作 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `{{title}}` | `{{doi}}` | `{{paper_type}}` | `{{method_or_data}}` | `{{key_result}}` | `{{evidence_strength}}` | `{{relevance_level}}` | `{{reading_priority}}` | `{{action}}` |

## 综合分析

### 共同趋势

说明这些论文共同体现出的技术趋势、研究范式变化、数据集或评测方式变化。

### 方法与数据格局

说明本批次论文主要使用了哪些方法、数据来源、样本类型、指标和比较方式。

### 分歧与不确定性

说明不同论文之间的观点冲突、实验结论差异、外部有效性问题，以及仍需验证的假设。

### 研究空白

说明这批论文共同没有解决、只部分触及或仍明显缺证据的问题。

### 对后续研究的启发

- 可复现或可借鉴的方法：`{{methods_to_reuse}}`
- 可以继续跟进的问题：`{{follow_up_questions}}`
- 值得优先阅读的论文：`{{priority_papers}}`

## 单篇论文摘要

> 保持索引化，避免重复单篇 `report.md` 的全部内容。

### `{{paper_title}}`

- DOI：`{{doi}}`
- 本地 PDF：`{{pdf_path}}`
- 本地 Markdown：`{{markdown_path}}`
- 一句话摘要：`{{one_sentence_summary}}`
- 最关键结果：`{{most_important_result}}`
- 相关性：`{{relevance_level}}`
- 单篇报告路径：`{{item_report_path}}`

## 失败条目

| 论文 | DOI | 状态 | 原因 | 建议处理 |
| --- | --- | --- | --- | --- |
| `{{title}}` | `{{doi}}` | `failed` | `{{reason}}` | `{{manual_action}}` |

## 需人工处理的条目

| 论文 | DOI | 状态 | 原因 | 建议处理 |
| --- | --- | --- | --- | --- |
| `{{title}}` | `{{doi}}` | `needsManual` | `{{reason}}` | `{{manual_action}}` |

## 已在 Zotero collection 中的条目

| 论文 | DOI | Zotero item key | 处理 |
| --- | --- | --- | --- |
| `{{title}}` | `{{doi}}` | `{{zotero_item_key}}` | 已跳过，不重复下载、归档或研究 |

## 附录

### PDF 下载规则候选

| 来源 | DOI | Landing URL | 触发方式 | 下载结果 | 建议规则文档 |
| --- | --- | --- | --- | --- | --- |
| `{{domain}}` | `{{doi}}` | `{{landing_url}}` | `{{download_trigger}}` | `{{download_result}}` | `{{suggested_rule_path}}` |

如果没有候选规则，写“无”。

- process items 文件：`{{process_items_path}}`
- 研究输出目录：`{{run_output_dir}}`
- PDF 下载规则候选文件：`{{pdf_download_rule_candidates_path}}`
- 备注：`{{notes}}`
