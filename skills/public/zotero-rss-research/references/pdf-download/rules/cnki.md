# 中国知网（CNKI）PDF 下载规则

## 匹配条件

- Domains:
  - `kns.cnki.net`
  - `www.cnki.net`

## 前提条件

**必须通过机构订阅访问**（如武汉大学图书馆代理 `whu.metaersp.cn` → CNKI）。
浏览器必须有有效的 CNKI 机构会话 cookie（会话过期时需重新通过机构代理登录）。

## Landing URL

- 示例：`https://kns.cnki.net/kcms2/article/abstract?v=tjV0JOkNcjAkml0nfzcqwuy-SbTJbXYIZ1QuXfpa3H69oMVFJfmo34HOwwzXRxgrn26F83qN0mvY7WY9PW5pmveqHlO7uBDIUvlC4HpLp2IHwUSpnd86zxPSU-up9r_O8_VFZcnPcOC4CffFcqoD-T3BkIjGlr30yJ-EBfkgLOM-kjTmwpfowQ==&uniplatform=NZKPT&language=CHS`
- 模式：`https://kns.cnki.net/kcms2/article/abstract?v={encrypted_session_param}&uniplatform=NZKPT&language=CHS`
- **注意**：RSS feed 中的 `v` 参数与当前 CNKI 会话不同，直接使用 feed URL 会触发验证码。必须通过搜索页面的当前会话 URL 访问文章。

## 下载方式

类型：`browser-click`

PDF 下载需要：
1. 有效的 CNKI 机构会话
2. 浏览到文章摘要页面
3. 点击页面上 "PDF下载" 链接（该链接有 `kns.cnki.net` referrer 验证）

PDF 下载链接格式为：`https://bar.cnki.net/bar/download/order?id={encrypted}`，不能通过 HTTP 请求或浏览器直接导航访问（会返回 "来源应用不正确" 错误）。

## 执行步骤

### 第 1 步：获取文章标题

从 Zotero feed item 的 title 字段获取文章标题。

```bash
zotero-cli feeds items {feed_id} --limit 1
```

### 第 2 步：在 CNKI 搜索页面上建立会话

打开 CNKI 个性化首页以建立/刷新会话：

```bash
openclaw browser open "https://kns.cnki.net/kns8s/" --label "cnki-session"
```

### 第 3 步：搜索文章

使用文章标题构造搜索 URL。需要 URL 编码标题（JavaScript `encodeURIComponent` 或等价的 shell 工具）：

```bash
openclaw browser navigate "{search_url}"  # 在 cnki-session tab 中
```

搜索 URL 模式：

```text
https://kns.cnki.net/kns8s/search?classid=WD0FTY92&kw={URL_ENCODED_TITLE}&korder=SU&language=CHS&uniplatform=NZKPT
```

如果搜索结果显示 0 条结果，尝试更简短的标题（去掉副标题，或用关键词子集搜索）。

### 第 4 步：提取文章摘要 URL

搜索页面通过 AJAX 动态加载结果。使用 `evaluate` 提取第一个匹配文章的链接：

```bash
openclaw browser evaluate --fn '() => {
  const links = document.querySelectorAll("\''a[href*=\"/kcms2/article/abstract\"]\''");
  return links.length > 0 ? links[0].href : null;
}'
```

如果提取到 `null`，等待页面加载后再重试。如果搜索返回多条结果，匹配标题最接近的那一条。

### 第 5 步：导航到文章摘要页面

```bash
openclaw browser navigate "{article_abstract_url}"
```

页面必须成功加载（应显示文章标题、作者、摘要等信息）。如果页面重定向到验证码（`/verify/home`），说明会话已失效，需要重新通过机构代理登录 CNKI。

### 第 6 步：提取 PDF 下载链接并触发下载

从文章页面提取 "PDF下载" 链接：

```bash
openclaw browser evaluate --fn '() => {
  const all = document.querySelectorAll("a");
  for (const a of all) {
    if (a.textContent.includes("PDF下载")) return a.href;
  }
  return null;
}'
```

如果提取到 PDF 链接，点击下载：

```bash
# 先记录 downloadDir 中的现有文件，然后：
openclaw browser evaluate --fn '() => {
  const all = document.querySelectorAll("a");
  for (const a of all) {
    if (a.textContent.includes("PDF下载")) { a.click(); return "clicked"; }
  }
  return "not found";
}'
```

### 第 7 步：验证下载

等待浏览器完成下载，然后在 downloadDir 中定位新文件：

```bash
# 对比下载前后的目录快照找到新文件
ls -lt "{downloadDir}" | head -5

# 验证文件是有效 PDF
file "{target_pdf_path}"
test -s "{target_pdf_path}"
```

## 下载产物定位

- 浏览器将文件下载到 `state/config.json` 的 `downloadDir`（当前配置为 `/tmp/openclaw/downloads`）。
- 通过目录快照差异定位新下载的 PDF。
- 原始文件名规则：`{uuid}-{title}_{author}.pdf`。UUID 前缀为浏览器生成，title 和 author 从页面标题提取。
- 原始文件名示例：
  - `5aa6055c-b28a-4a59-916c-30000afcc11d-时空信息显式引导的高分光学遥感影像可控生成方法_时天东.pdf`
  - `4cddc1e9-10af-4810-aeec-b8cc0ac967fd-论地理信息保密的技术逻辑_刘万增.pdf`
  - `e0aa3b49-ca15-466e-bca0-5467dac03c80-基于船舶轨迹大数据的多港口聚集海湾原油运量监测_高山林.pdf`
- 作者姓名从 Zotero feed item 的 creators 字段可以预先获取，用于验证下载结果。
- 文件名不可作为唯一定位依据；以目录快照差异和 PDF 文件门禁为准。

## 失败条件

### 会话失效（验证码拦截）

如果文章导航跳转到 `/verify/home`（验证码页面），CNKI 会话已过期：

```text
status=needsManual
failureStage=navigation
lastError=CNKI session expired; re-authenticate via institutional proxy (whu.metaersp.cn)
```

### 文章仅提供 CAJ 格式（无 PDF）

CNKI 部分文章只提供 CAJ 下载，不提供 PDF（如中文期刊的早期论文）：

```text
status=failed
failureStage=pdf_extract
lastError=Only CAJ download available for this article; no PDF option on detail page
```

### PDF 下载链接未找到且页面正常加载

文章页面加载成功但没有 "PDF下载" 也没有 "CAJ下载" 链接：

```text
status=failed
failureStage=pdf_extract
lastError=No download links found on article page
```

### 下载未完成

下载链接已点击但下载目录中未出现新 PDF：

```text
status=failed
failureStage=download
lastError=PDF download not found in downloadDir after click; check browser download status
```

### 文件未通过 PDF 门禁

下载的文件存在但不是有效 PDF：

```text
status=failed
failureStage=verify
lastError=Downloaded file failed PDF validation: {reason}
```

### CNKI 搜索无结果

```text
status=failed
failureStage=search
lastError=Article not found in CNKI search: {title}. Try shorter title or keyword subset.
```

## 测试验证

已通过以下文章验证下载流程（覆盖测绘学报和地球信息科学学报两个 feed）：

| # | 文章标题 | 来源 | 状态 |
|---|---------|------|------|
| 1 | 时空信息显式引导的高分光学遥感影像可控生成方法 | 测绘学报 | ✅ PDF 15页 5.6MB |
| 2 | 论地理信息保密的技术逻辑 | 测绘学报 | ✅ PDF 1.5MB |
| 3 | GNSS精密单点定位增强技术研究 | 测绘学报 | ⚠️ CAJ only |
| 4 | 融合矢量结构特征的复杂建筑物形状识别方法 | 测绘学报 | ✅ PDF link confirmed |
| 5 | 基于船舶轨迹大数据的多港口聚集海湾原油运量监测 | 地球信息科学学报 | ✅ PDF 24页 3.8MB |

## 注意事项

1. **会话有效期**：CNKI 机构会话有超时限制，长时间不活动会失效。如果浏览器到 CNKI 新页面时出现验证码，需要重新通过机构代理登录。
2. **加载延迟**：CNKI 页面较复杂，导航后需要等待 AJAX 结果加载完成再提取链接。
3. **编码问题**：搜索 URL 中文章标题必须正确 URL 编码（UTF-8）。
4. **同名校验**：如果搜索返回多条结果，需用 Zotero 中的 DOI、作者名、journal 名等信息验证匹配。
5. **本文规则只测试跨域下载**：需要通过 `whu.metaersp.cn` 代理才能获取下载权限；外网直接访问 CNKI 无法免费下载全文。
