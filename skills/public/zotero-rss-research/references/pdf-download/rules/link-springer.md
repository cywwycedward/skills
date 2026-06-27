# Springer Nature Link PDF 下载规则

## 匹配条件

- Domains:
  - `link.springer.com`

## Landing URL

- 示例：`https://link.springer.com/article/10.1007/s10707-026-00579-x`
- 模式：`https://link.springer.com/article/{doi}`

## 下载方式

类型：`browser-open`

打开 PDF URL 后，在同一浏览器 tab 中用浏览器会话执行 `fetch(window.location.href)`，再以 blob 触发下载。不要使用 `curl` 或 `curl + browser cookies`；实测稳定性不足，可能返回 HTML landing page 或空响应。

## 执行步骤

1. 从条目 DOI 构造 PDF URL：`https://link.springer.com/content/pdf/{doi}.pdf`
2. 执行前记录 `downloadDir` 当前文件列表。
3. 用 OpenClaw browser 打开 PDF URL：

```bash
openclaw browser open "https://link.springer.com/content/pdf/{doi}.pdf"
```

4. 在该 PDF tab 中执行 blob 下载：

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
    a.download = "{sanitized_doi}.pdf";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 3000);
    return JSON.stringify({ok:true, size:blob.size, type:blob.type || type});
  } catch (e) {
    return JSON.stringify({ok:false, stage:"exception", error:e.message});
  }
}'
```

## 下载产物定位

- 浏览器将文件下载到 `state/config.json` 的 `downloadDir`。
- 下载后定位新增且大小稳定的 PDF，通过 PDF 文件门禁后移动到 `{target_pdf_path}`。
- 原始文件名规则：通常为 `{uuid}-{sanitized_doi}.pdf`，由 blob download 触发，UUID 前缀为 Chrome 生成。
- 原始文件名示例：`751371e4-14e6-49ce-8ed2-c9f0c5752240-10.1007_s10707-026-00579-x.pdf`
- 文件名不可作为唯一定位依据；以目录快照差异和 PDF 文件门禁为准。

## 失败条件

- 浏览器打开 PDF URL 后无法加载，或 `fetch(window.location.href)` 返回非 2xx：

```text
status=failed
failureStage=download
lastError=Springer PDF fetch failed for {doi}: {reason}
```

- 下载目录中没有新增稳定 PDF，或新增文件未通过 PDF 文件门禁：

```text
status=failed
failureStage=verify
lastError=file did not pass PDF gate for {doi}: {reason}
```

- 页面显示登录、订阅、付费、验证码、无权限或 session 失效：

```text
status=needsManual
failureStage=download
lastError=Springer access or session required for {doi}: {reason}
```
