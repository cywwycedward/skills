# {平台名称} PDF 下载规则

## 匹配条件

- Domains:
  - `{domain}`

## Landing URL

- 示例：`{landing_url_example}`
- 模式：`{landing_url_pattern}`

## 下载方式

类型：`http-client|browser-open|browser-click|manual-required`

## 执行步骤

1. `{step_1}`
2. `{step_2}`
3. 执行：

```bash
{download_command}
```

## 下载产物定位

- 命令直写路径 / 浏览器下载目录观察方式：`{artifact_location_method}`
- 原始文件名规则：`{filename_pattern}`
- 原始文件名示例：`{filename_example}`
- 如果不可稳定预测：写“不可稳定预测”。

## 失败条件

- `{manual_or_failure_condition}`
- 需要人工处理时记录：

```text
status=needsManual
failureStage=download
lastError={reason}
```
