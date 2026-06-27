# Taylor & Francis PDF 下载规则

## 匹配条件

- Domains:
  - `www.tandfonline.com`

## Landing URL

- 示例：`https://www.tandfonline.com/doi/full/10.1080/13658816.2026.2686261?af=R`
- 模式：`https://www.tandfonline.com/doi/full/{doi}` 或 `https://www.tandfonline.com/doi/abs/{doi}`

## 下载方式

类型：`browser-open`

打开 Taylor & Francis epdf viewer 后，在该浏览器 session 中用 `fetch()` 获取 `/doi/pdf/{doi}?download=true`，并通过 blob 触发下载。不要直接 `openclaw browser open` PDF 下载 URL；该路径依赖原生下载事件，实测可能出现空 tab、无文件落盘或下载事件丢失。

## 执行步骤

1. 从 RSS item URL 或 DOI 提取 DOI。URL 中的 DOI 是 `/doi/full/` 或 `/doi/abs/` 后、查询参数前的部分，例如 `10.1080/13658816.2026.2686261`。

2. 执行前记录 `state/config.json` 的 `downloadDir` 当前文件列表。

3. 在浏览器中打开 epdf viewer 页面：

```bash
openclaw browser open "https://www.tandfonline.com/doi/epdf/{doi}?needAccess=true"
```

4. 等待 viewer 加载完成。页面 snapshot 中应出现 `Page X / Y`：

```bash
openclaw browser snapshot --compact | grep -E "Page [0-9]+ / [0-9]+"
```

如 snapshot 未显示页码，可用 DOM 检查 PDF 链接是否存在：

```bash
openclaw browser evaluate --fn '() => JSON.stringify({hasPdfLink: !!document.querySelector("a[href*=\"/doi/pdf/\"]")})'
```

5. 在 epdf viewer tab 中启动后台 blob 下载。`openclaw browser evaluate` 不要等待整个 PDF fetch 完成；较大 PDF 会超过 evaluate 固定超时，但下载仍会成功落盘。

```bash
openclaw browser evaluate --fn '() => {
  window.__tfBlobDownloadStatus = {state:"started", ts:Date.now()};
  (async () => {
    try {
      const m = window.location.pathname.match(/\/doi\/epdf\/([^?]+)/);
      if (!m) {
        window.__tfBlobDownloadStatus = {state:"failed", stage:"doi", error:"no DOI in epdf URL"};
        return;
      }
      const doi = decodeURIComponent(m[1]);
      const resp = await fetch("/doi/pdf/" + doi + "?download=true", {credentials:"include"});
      const type = resp.headers.get("content-type") || "";
      const dispo = resp.headers.get("content-disposition") || "";
      if (!resp.ok) {
        window.__tfBlobDownloadStatus = {state:"failed", stage:"fetch", status:resp.status, type, dispo};
        return;
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "{sanitized_doi}.pdf";
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        try { document.body.removeChild(a); } catch (e) {}
        URL.revokeObjectURL(url);
      }, 3000);
      window.__tfBlobDownloadStatus = {state:"clicked", ok:true, size:blob.size, type:blob.type || type, dispo};
    } catch (e) {
      window.__tfBlobDownloadStatus = {state:"failed", stage:"exception", error:e.message};
    }
  })();
  return JSON.stringify(window.__tfBlobDownloadStatus);
}'
```

6. 下载期间可检查页面状态：

```bash
openclaw browser evaluate --fn '() => JSON.stringify(window.__tfBlobDownloadStatus || null)'
```

7. 下载后定位新增且大小稳定的 PDF，通过 PDF 文件门禁后移动到 `{target_pdf_path}`。

## 下载产物定位

- 浏览器将文件下载到 `state/config.json` 的 `downloadDir`（当前配置为 `/tmp/openclaw/downloads`）。
- 执行步骤 5 前后比较 `downloadDir` 文件列表，定位新增且大小稳定的 PDF；不要依赖固定文件名定位。
- 原始文件名规则：通常为 `{uuid}-{sanitized_doi}.pdf`，由 blob download 触发，UUID 前缀为 Chrome 生成。
- 原始文件名示例：`e5cb7e13-c1f6-4f65-bb20-63b332a19551-10.1080_13658816.2026.2686261.pdf`
- 此方法已在 20 个 Taylor & Francis feed item 上验证成功，PDF 大小约 `1.8MB` 到 `25MB`。

## 失败条件

- epdf viewer 30 秒内未出现 `Page X / Y` 或 `/doi/pdf/` 链接，且页面显示登录、订阅、付费、验证码、无权限或 session 失效：

```text
status=needsManual
failureStage=load
lastError=Taylor & Francis access or session required for {doi}: {reason}
```

- epdf viewer 30 秒内未出现 `Page X / Y` 或 `/doi/pdf/` 链接，且页面没有明确权限限制：

```text
status=failed
failureStage=load
lastError=epdf viewer did not load within 30s for {doi}
```

- `window.__tfBlobDownloadStatus.state` 为 `failed`，或 `fetch()` 返回非 2xx：

```text
status=failed
failureStage=download
lastError=Taylor & Francis blob fetch failed for {doi}: {reason}
```

- 下载目录中没有新增稳定 PDF，或新增文件未通过 PDF 文件门禁：

```text
status=failed
failureStage=verify
lastError=file did not pass PDF gate for {doi}: {reason}
```
