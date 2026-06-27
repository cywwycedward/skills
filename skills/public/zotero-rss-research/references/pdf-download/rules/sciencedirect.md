# Elsevier ScienceDirect PDF 下载规则

## 匹配条件

- Domains:
  - `www.sciencedirect.com`

## Landing URL

- 示例：`https://www.sciencedirect.com/science/article/pii/S0198971526000554`
- 模式：`https://www.sciencedirect.com/science/article/pii/{PII}`

## 下载方式

类型：`browser-open`

打开 landing page 提取 `/pdfft` 链接，再在 PDF tab 中用浏览器会话执行 blob fetch 下载。

## 执行步骤

1. 从条目 URL 提取 PII：URL 中的 `/pii/{PII}` 部分，例如 `S0198971526000554`。
2. 在浏览器中打开 landing page：

```bash
openclaw browser open "https://www.sciencedirect.com/science/article/pii/{PII}" --label "sd-{PII_short}"
```

3. 从 landing page 提取 pdfft URL（"View PDF" 链接的 href）：

```bash
openclaw browser evaluate --fn 'document.querySelector("a[href*=\"/pdfft\"]")?.href || ""'
```

4. 如果没有 pdfft URL，按失败条件记录并停止。

5. 使用 `openclaw browser open` 在新 tab 中打开 pdfft URL（不要用 `openclaw browser navigate`，navigate 在当前 tab 改 URL 会被页面状态/脚本干扰导致失败）：

```bash
openclaw browser open "{pdfft_url}"
```

6. 等待 PDF 加载（新 tab 完成 S3 重定向后），在 PDF tab 中通过 JavaScript blob fetch 触发下载：

```bash
openclaw browser evaluate --fn 'async () => {
  try {
    const resp = await fetch(window.location.href);
    const type = resp.headers.get("content-type") || "";
    if (!resp.ok) return JSON.stringify({ok:false, stage:"fetch", status:resp.status, type});
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "{PII}.pdf";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 3000);
    return JSON.stringify({ok:true, size:blob.size, type:blob.type || type});
  } catch(e) {
    return JSON.stringify({ok:false, stage:"exception", error:e.message});
  }
}'
```

## 下载产物定位

- 浏览器将文件下载到 `state/config.json` 的 `downloadDir`（当前配置为 `/tmp/openclaw/downloads`）。
- 执行步骤 6 前记录 `downloadDir` 文件列表；下载后定位新增且大小稳定的 PDF，通过 PDF 文件门禁后移动到 `{target_pdf_path}`。
- 原始文件名规则：通常为 `{uuid}-{PII}.pdf`，由 blob download 触发，UUID 前缀为 Chrome 生成。
- 原始文件名示例：`39ef749c-cf74-4ad9-bae2-d416c7e4c0bc-S0198971526000554.pdf`
- 文件名不可作为唯一定位依据；以目录快照差异和 PDF 文件门禁为准。

## 失败条件

- pdfft URL 未找到，且页面显示登录、订阅、付费、无权限或 session 失效：

```text
status=needsManual
failureStage=download
lastError=pdfft URL not found; access or session required for {PII}
```

- pdfft URL 未找到，且页面没有明确权限限制：

```text
status=failed
failureStage=pdfft_extract
lastError=pdfft URL not found on landing page for {PII}
```

- `openclaw browser open` pdfft 后未重定向到 S3 PDF（可能被反爬虫验证拦截）：

```text
status=failed
failureStage=navigation
lastError=did not reach S3 PDF for {PII}
```

- blob fetch 失败（PDF 过大、超时、网络错误）：

```text
status=failed
failureStage=download
lastError=blob fetch failed for {PII}: {reason}
```

- 下载目录中没有新增稳定 PDF，或新增文件未通过 PDF 文件门禁：

```text
status=failed
failureStage=verify
lastError=file did not pass PDF gate for {PII}: {reason}
```
