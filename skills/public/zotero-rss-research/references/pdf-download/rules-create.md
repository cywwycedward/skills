# PDF 下载规则创建流程

只在用户明确要求添加、创建或优化平台 PDF 下载规则时执行。Cron 不执行本流程。

## 输入

- 平台 domain。
- 一个或多个真实 landing URL。
- DOI、title 或其他可用于确认目标论文的字段。
- 测试保存路径：`{target_pdf_path}`。

## 起草

1. 读取 `references/pdf-download/rule-template.md`。
2. 读取 `state/config.json`，确认 `downloadDir`。
3. 基于真实页面和工具状态探索下载方式；不要为了满足固定顺序而重复无意义尝试。
4. 规则目标路径使用 `references/pdf-download/rules/{platform-or-domain}.md`。
5. 规则只保留本平台实际采用的一种下载方式。

## 示例探索方案

以下是可选方案，不是强制顺序。选择最稳定、可复现、最少依赖临时状态的方式。

### http-client

适用于 PDF URL 可稳定推导，且 `curl` 或 `wget` 可直接写入 `{target_pdf_path}` 的平台。
规则必须写完整命令；需要 header、cookie、referer 或固定参数时，也写在平台规则中。

```bash
curl -L "{pdf_url}" -o "{target_pdf_path}"
wget -O "{target_pdf_path}" "{pdf_url}"
```

### browser-open

适用于 PDF URL 可稳定推导，但下载必须依赖浏览器会话的场景。执行浏览器打开后，从
`state/config.json` 的 `downloadDir` 观察新下载文件，确认平台的原始文件名规则，再移动到
`{target_pdf_path}`。

```bash
openclaw browser open "{pdf_url}"
```

如果只是打开 PDF 预览页但没有落盘，不算可行规则。

### browser-click

适用于必须通过页面按钮或链接触发下载的场景。规则必须描述如何稳定找到下载入口，例如按钮
文字、链接 href、aria label 或页面结构；不要把单次运行的临时 `ref` 当作稳定规则。

如果下载入口可直接触发下载，优先使用：

```bash
openclaw browser download "{ref}" "{target_pdf_path}" --timeout-ms 120000
```

如果必须由普通点击触发下载，先启动等待，再点击：

```bash
openclaw browser waitfordownload "{target_pdf_path}" --timeout-ms 120000
openclaw browser click "{ref}"
```

### manual-required

适用于需要登录、验证码、机构权限、付费权限或人工确认的场景。规则中写明原因，并记录：

```text
status=needsManual
failureStage=download
lastError={reason}
```

## 验收标准

规则完成前必须满足：

- 至少用一个真实 landing URL 测试过。
- PDF 实际下载到 `{target_pdf_path}`，或能从配置下载目录稳定定位并移动到该路径。
- 文件存在、非空，并通过 `references/pdf-download/rules-execution.md` 的 PDF 文件门禁。
- 文件确认为目标论文：可用文件名、标题、DOI、页面元数据或转换后的 Markdown 核对。
- 下载方式稳定：至少重复成功两次，或有等价证据证明不是一次性临时链接。
- 匹配只依赖 domain 和稳定页面特征，不依赖单篇论文的临时 `ref`。
- 规则写明下载产物定位方式和原始文件名规则；不可稳定预测时明确写“不可稳定预测”。
- 单看该规则文件即可执行下载，不依赖其他平台规则文档补充步骤。

下载后至少执行：

```bash
test -s "{target_pdf_path}"
file "{target_pdf_path}"
```

如需进一步确认目标论文，可执行：

```bash
markitdown "{target_pdf_path}" -o "{target_md_path}"
```

## 最终写入门禁

规则已经完成设计、实际下载测试、文件门禁和目标论文核验后，先向用户汇报：

- domain
- landing URL 示例
- 下载方式
- 精确命令或浏览器动作
- 下载目录和文件名识别方式
- 验收证据
- 目标规则文件路径

只有用户确认后，才写入或更新 `references/pdf-download/rules/*.md` 和
`references/pdf-download/rules-execution.md` 的平台索引。
