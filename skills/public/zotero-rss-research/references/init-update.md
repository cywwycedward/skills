# Zotero RSS 初始化与配置更新

只在交互式用户会话中初始化或更新配置。不要在 cron 中初始化或更新。

## 初始化

1. 检查本地工具链：

   ```bash
   zotero-cli --version
   zotero-cli config validate
   zotero-cli feeds list
   markitdown --version
   ```

2. 和用户确认配置：
   - collection 名称
      - 使用 `zotero-cli collections list` 检查是否存在该 collection。
      - 如果 collection 存在，记录 collection key。
      - 如果 collection 不存在，询问用户是否创建。
      - 如果用户同意创建，使用 `zotero-cli collections create --name "<collectionName>"` 创建，并记录 collection key。
      - 如果用户拒绝创建，停止并等待用户提供有效 collection 名称。
   - feed_id
      - 使用 `zotero-cli feeds list` 列出所有 feeds，询问用户选择要包含的 feed。
      - 将用户选择的 feed_id 记录在配置中。
   - 报告语言
      - 默认 `zh-CN`。
      - 将用户选择的语言记录在配置中。
   - 下载目录
      - 默认 `/tmp/openclaw/downloads`。
      - 将用户提供的下载目录路径记录在配置中。
   - 回补窗口
      - 默认 `lookbackDays: 7`。
      - 用于 cron 每次回看最近 N 天，并通过 Zotero collection DOI 去重避免重复处理。

3. 写入 `state/config.json`：

   ```json
   {
     "collectionName": "daily",
     "collectionKey": "WUHL3RII",
     "feeds": ["2"],
     "downloadDir": "/tmp/openclaw/downloads",
     "reportLanguage": "zh-CN",
     "lookbackDays": 7
   }
   ```

## 更新

当用户需要更新配置时，提供交互式选择：

- collection 名称 / collection key
- feed_id
- 报告语言
- 下载目录
- 回补窗口 `lookbackDays`

更新后重新验证：

```bash
zotero-cli config validate
zotero-cli feeds list
markitdown --version
```
