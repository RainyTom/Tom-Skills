---
name: doc-to-markdown
description: "通过 MinerU 精准解析 API 将 PDF/图片/Office/HTML 等多种格式文档转换为 Markdown。需 Token，支持单文件/批量/URL/本地文件上传，YAML 配置管理密钥。触发词：文档转md、anything-to-markdown、mineru、文档转换、extract task、图片转md、word转md、ppt转md。"
allowed-tools:
  - Read
  - Write
  - Edit
  - RunInTerminal
  - AskUserQuestion
metadata:
  trigger: 将任意格式文档（PDF/图片/Office/HTML）转为 Markdown
---

# 文档转 Markdown — MinerU 精准解析 API

通过 MinerU 精准解析 API 将 PDF、图片、Office 文档等转换为 Markdown 格式。需在 Header 中填写 Token，支持单文件/批量、URL/本地文件上传，使用 YAML 文件管理配置。转换返回 Zip 结果包，解压后提取 `full.md`。

## 使用场景

- 将 PDF/图片/Word/PPT/HTML 等文档转换为 Markdown
- 通过 URL 提交远程文件，或批量上传本地文件
- 批量解析多个文档（批量 URL 模式 / 批量文件上传模式）
- 需要公式识别、表格识别、多语言 OCR 的文档解析

## 使用方法

### 工作流程概览

```
用户输入文件/URL
    │
    ▼
选择提交方式 ───┬── URL 提交（远程文件链接）
                └── 本地文件批量上传（签名上传到 OSS）
    │
    ▼
轮询等待解析完成
    │
    ▼
获取 Zip 结果包 → 提取 Markdown
```

优先使用 `scripts/anything_to_markdown.py` 封装脚本（自动处理配置读取、轮询、结果下载）；需要精细控制时直接调用 HTTP API。

### 命令行使用

```bash
# 精准解析 API - URL 模式（需要 token）
python3 scripts/anything_to_markdown.py precision-url \
  --url "https://cdn-mineru.openxlab.org.cn/demo/example.pdf" \
  --model vlm \
  --output ./output/

# 精准解析 API - 批量 URL 模式
python3 scripts/anything_to_markdown.py precision-batch-url \
  --files '[{"url":"https://example.com/a.pdf","data_id":"a"},{"url":"https://example.com/b.pdf","data_id":"b"}]' \
  --model vlm \
  --output ./output/

# 精准解析 API - 本地文件批量上传
python3 scripts/anything_to_markdown.py precision-batch-file \
  --files ./doc1.pdf ./doc2.pdf \
  --model vlm \
  --output ./output/

# 初始化配置文件
python3 scripts/anything_to_markdown.py config init

# 查看当前配置
python3 scripts/anything_to_markdown.py config show
```

### Python 脚本快速转换

```python
from scripts.anything_to_markdown import MinerUConverter

# 自动从 YAML / 环境变量读取 token
converter = MinerUConverter()

# --- 精准解析 API - URL 提交 ---
result = converter.parse_url_precision(
    url="https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    model_version="vlm"
)
# result 是 Zip 包 URL，需下载解压
print(result["full_zip_url"])

# --- 精准解析 API - 批量 URL 提交 ---
results = converter.parse_url_batch(
    files=[
        {"url": "https://example.com/doc1.pdf", "data_id": "doc1"},
        {"url": "https://example.com/doc2.pdf", "data_id": "doc2"},
    ],
    model_version="vlm"
)

# --- 精准解析 API - 本地文件批量上传 ---
results = converter.parse_file_batch(
    file_paths=["./doc1.pdf", "./doc2.pdf"],
    model_version="vlm"
)
```

## 详细指南

### 配置文件管理

密钥和默认配置通过 YAML 文件管理。用户需先创建配置文件。

#### 配置文件位置

| 路径                                           | 说明                                 |
| ---------------------------------------------- | ------------------------------------ |
| `<skill_dir>/config.yaml`（即本 SKILL 目录下） | 默认配置（推荐，随技能一起管理）     |
| `./.anything-to-markdown.yaml`                 | 项目级配置（优先级更高，适合 CI/CD） |

#### 配置文件格式

```yaml
# <skill_dir>/config.yaml（即 skills/doc-to-markdown/config.yaml）
mineru:
  # 精准解析 API Token（在 https://mineru.net 的 API 管理页面创建）
  token: "your-mineru-token-here"

  # 默认参数（可被函数调用覆盖）
  default_model: "vlm" # pipeline | vlm | MinerU-HTML
  default_language: "ch" # 见 language 取值参考
  default_enable_table: true
  default_enable_formula: true
  default_is_ocr: false

  # 轮询设置
  poll_interval: 3 # 轮询间隔（秒）
  poll_timeout: 300 # 轮询超时（秒）
```

> **首次使用**：运行 `python3 scripts/config_manager.py init` 交互式创建配置文件（默认保存在 SKILL 目录下）。

#### 通过环境变量覆盖 Token

```bash
export MINERU_TOKEN="your-token-here"
```

环境变量优先级高于 YAML 配置文件。

### 精准解析 API 详解

#### 单文件 URL 解析

```python
import requests
import time
from scripts.config_manager import ConfigManager

config = ConfigManager()
token = config.get_token()

url = "https://mineru.net/api/v4/extract/task"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
data = {
    "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    "model_version": "vlm"       # pipeline | vlm | MinerU-HTML
}

# 1. 提交任务
resp = requests.post(url, headers=headers, json=data)
task_id = resp.json()["data"]["task_id"]

# 2. 轮询结果
query_url = f"https://mineru.net/api/v4/extract/task/{task_id}"
while True:
    resp = requests.get(query_url, headers=headers)
    result = resp.json()["data"]
    state = result["state"]
    if state == "done":
        zip_url = result["full_zip_url"]
        print(f"下载链接: {zip_url}")
        break
    elif state == "failed":
        raise Exception(result.get("err_msg", "解析失败"))
    time.sleep(config.get("poll_interval", 3))
```

#### 本地文件批量上传解析

```python
import requests
from scripts.config_manager import ConfigManager

config = ConfigManager()
token = config.get_token()

# 1. 申请上传链接
url = "https://mineru.net/api/v4/file-urls/batch"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
data = {
    "files": [{"name": "demo.pdf", "data_id": "doc1"}],
    "model_version": "vlm"
}
resp = requests.post(url, headers=headers, json=data)
result = resp.json()
batch_id = result["data"]["batch_id"]
upload_urls = result["data"]["file_urls"]

# 2. 上传文件到 OSS
for i, upload_url in enumerate(upload_urls):
    with open("demo.pdf", "rb") as f:
        requests.put(upload_url, data=f)

# 3. 批量查询结果
query_url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
# ... 轮询直到所有任务完成
```

#### 批量 URL 解析

```python
import requests

url = "https://mineru.net/api/v4/extract/task/batch"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
data = {
    "files": [
        {"url": "https://example.com/doc1.pdf", "data_id": "doc1"},
        {"url": "https://example.com/doc2.pdf", "data_id": "doc2"},
    ],
    "model_version": "vlm"
}
resp = requests.post(url, headers=headers, json=data)
batch_id = resp.json()["data"]["batch_id"]
```

#### 请求参数说明（精准解析 API）

| 参数               | 类型     | 必填 | 默认值     | 说明                                                                |
| ------------------ | -------- | ---- | ---------- | ------------------------------------------------------------------- |
| `url`              | string   | 是   | -          | 文件 URL（单文件）或 `files[].url`（批量 URL）                      |
| `model_version`    | string   | 否   | `pipeline` | `pipeline` / `vlm` / `MinerU-HTML`（HTML 文件必须用 `MinerU-HTML`） |
| `is_ocr`           | bool     | 否   | `false`    | 是否启用 OCR。仅 pipeline/vlm 有效                                  |
| `enable_formula`   | bool     | 否   | `true`     | 是否开启公式识别。仅 pipeline/vlm 有效                              |
| `enable_table`     | bool     | 否   | `true`     | 是否开启表格识别。仅 pipeline/vlm 有效                              |
| `language`         | string   | 否   | `ch`       | 文档语言。见 language 取值参考                                      |
| `data_id`          | string   | 否   | -          | 业务数据 ID（≤128 字符）                                            |
| `page_ranges`      | string   | 否   | -          | 页码范围，如 `"2,4-6"` 或 `"2--2"`                                  |
| `callback`         | string   | 否   | -          | 回调 URL（不填则需轮询）                                            |
| `seed`             | string   | 否   | -          | 回调签名随机字符串（配合 callback）                                 |
| `extra_formats`    | [string] | 否   | -          | 额外导出格式：`docx` / `html` / `latex`                             |
| `no_cache`         | bool     | 否   | `false`    | 是否绕过缓存                                                        |
| `cache_tolerance`  | int      | 否   | `900`      | 缓存容忍时间（秒）                                                  |
| `file.name`        | string   | 是   | -          | 文件名（批量上传时用 `files[].name`）                               |
| `file.is_ocr`      | bool     | 否   | `false`    | 单个文件的 OCR 设置（批量上传）                                     |
| `file.data_id`     | string   | 否   | -          | 单个文件的数据 ID（批量上传）                                       |
| `file.page_ranges` | string   | 否   | -          | 单个文件的页码范围（批量上传）                                      |

### 结果处理

精准解析 API 返回 Zip 压缩包 URL，解压后包含：

| 文件                  | 说明                             |
| --------------------- | -------------------------------- |
| `full.md`             | Markdown 解析结果                |
| `layout.json`         | 中间处理结果（原 `middle.json`） |
| `*_model.json`        | 模型推理结果                     |
| `*_content_list.json` | 内容列表                         |
| `main.html`           | 提取后正文（仅 HTML 源文件）     |

```python
import requests
import zipfile
import io

# 下载并解压
resp = requests.get(zip_url)
z = zipfile.ZipFile(io.BytesIO(resp.content))
z.extractall("./output_dir/")

# 读取 Markdown
with open("./output_dir/full.md", "r") as f:
    md_content = f.read()
```

### 错误处理

| 错误码   | 说明                 | 处理方式                                           |
| -------- | -------------------- | -------------------------------------------------- |
| `A0202`  | Token 错误           | 检查 Token 格式（需 `Bearer ` 前缀）或更换新 Token |
| `A0211`  | Token 过期           | 在 API 管理页面重新创建 Token                      |
| `-500`   | 传参错误             | 检查参数类型及 `Content-Type`                      |
| `-60005` | 文件大小超出限制     | 文件最大 200MB                                     |
| `-60006` | 文件页数超过限制     | 文件最大 200 页                                    |
| `-60003` | 文件读取失败         | 检查文件是否损坏                                   |
| `-60008` | 文件读取超时         | 检查 URL 是否可访问（github/aws 等国外 URL 会超时）|
| `-60018` | 每日解析任务数达上限 | 次日再试                                           |
| `-60019` | HTML 文件解析额度不足 | 次日再试                                           |

### Language 取值参考

| 值            | 适用语言                                    |
| ------------- | ------------------------------------------- |
| `ch`          | 中文、英文、繁体中文（默认）                |
| `ch_server`   | 中文、英文、繁体中文、日文（含繁体/手写体） |
| `en`          | 纯英文                                      |
| `japan`       | 日文为主                                    |
| `korean`      | 韩文                                        |
| `chinese_cht` | 繁体中文为主                                |
| `latin`       | 拉丁语系（法语、德语、西班牙语等）          |
| `arabic`      | 阿拉伯语系                                  |
| `cyrillic`    | 西里尔语系                                  |
| `devanagari`  | 天城文语系                                  |

## 示例

### 场景 1：URL 文档转换为 Markdown

用户说「把这个 PDF 转成 Markdown：https://cdn-mineru.openxlab.org.cn/demo/example.pdf」→ 用 `parse_url_precision` 提交 URL 任务，下载解压结果：

```python
from scripts.anything_to_markdown import MinerUConverter

converter = MinerUConverter()
result = converter.parse_url_precision(
    url="https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    model_version="vlm",
    enable_table=True,
    enable_formula=True
)
# 下载并解压结果
import requests, zipfile, io
resp = requests.get(result["full_zip_url"])
z = zipfile.ZipFile(io.BytesIO(resp.content))
z.extractall("./output/")
print("转换完成 → ./output/full.md")
```

### 场景 2：批量转换（URL 模式）

用户说「把这几个文档链接批量转换」→ 用 `parse_url_batch` 一次提交多个 URL：

```python
from scripts.anything_to_markdown import MinerUConverter

converter = MinerUConverter()
results = converter.parse_url_batch(
    files=[
        {"url": "https://example.com/doc1.pdf", "data_id": "doc1"},
        {"url": "https://example.com/doc2.pdf", "data_id": "doc2"},
    ],
    model_version="vlm"
)
```

### 场景 3：本地文件批量上传

用户说「把目录里的本地文档转成 Markdown」→ 用 `parse_file_batch` 上传本地文件：

```python
from scripts.anything_to_markdown import MinerUConverter

converter = MinerUConverter()
result = converter.parse_url_precision(
    url="https://example.com/large-doc.pdf",
    model_version="vlm",
    enable_table=True,
    enable_formula=True
)
# 下载并解压结果
import requests, zipfile, io
resp = requests.get(result["full_zip_url"])
z = zipfile.ZipFile(io.BytesIO(resp.content))
z.extractall("./output/")
```

## 注意事项

1. **Token 安全**：Token 具有完全的操作权限，不要提交到版本控制系统。建议将 `<skill_dir>/config.yaml` 加入 `.gitignore` 或妥善管理文件权限。
2. **网络限制**：MinerU 服务器无法访问 GitHub、AWS 等国外 URL，请使用国内可访问的链接。
3. **HTML 文件**：解析 HTML 文件时必须设置 `model_version: "MinerU-HTML"`。
4. **缓存**：精准 API 默认使用 URL 缓存（15 分钟），设置 `no_cache: true` 可获取最新内容。
5. **文件格式**：文件名必须带有正确的后缀名，否则会检测失败。
6. **文件上传有效期**：申请的上传链接有效期为 24 小时。
