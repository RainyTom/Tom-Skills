---
name: zotero-interact
description: "通过 Zotero 本地 API（http://127.0.0.1:23119/api/）与 Zotero 文献管理器交互。用于：检索/获取条目、管理收藏集、增删改参考文献、导出引用、查询标签、同步文库以及自动化文献工作流。触发词：citation, reference, bibliography, zotero, paper, article, PDF, collection, tag, library, DOI, ISBN, PubMed。"
---

# Zotero 本地 API 交互

通过 Zotero 的 REST API 与本机运行的 Zotero 实例交互。Zotero 本地 API 运行在 `http://127.0.0.1:23119/api/`，要求 Zotero 已在同一台机器上启动。

## 使用场景

- 检索并获取 Zotero 文库条目（文章、书籍、论文等）
- 在 Zotero 中增删改参考文献
- 管理收藏集（collections）和标签（tags）
- 以多种格式导出引用（BibTeX、RIS、CSL JSON 等）
- 按 DOI、ISBN、PMID 或 arXiv ID 查询条目
- 批量处理文库元数据
- 以编程方式生成参考文献列表

## 使用方法

优先使用辅助脚本 `./scripts/zotero.py` 完成常见操作，再用裸 `curl` 处理脚本未覆盖的高级操作。先运行前置检查确认 Zotero 已启动。

```bash
# 前置检查：确认 Zotero 运行中且 API 可访问
curl -s http://127.0.0.1:23119/api/items?limit=1 | head -c 200

# 按标题、作者、年份等检索条目
python ./scripts/zotero.py search "deep learning"

# 列出最近条目（默认 10 条）
python ./scripts/zotero.py list --limit 20

# 按 itemKey 获取条目详情
python ./scripts/zotero.py get ITEMKEY123

# 新增条目（期刊文章）
python ./scripts/zotero.py add --type journalArticle --title "..." --creators "Author, First" --date "2024" --doi "10.1234/..."

# 按 DOI 添加条目（自动抓取元数据）
python ./scripts/zotero.py fetch-doi "10.1000/xyz123"

# 列出收藏集
python ./scripts/zotero.py collections

# 列出某收藏集内的条目
python ./scripts/zotero.py collection-items COLLECTIONKEY

# 列出所有标签
python ./scripts/zotero.py tags

# 导出 BibTeX
python ./scripts/zotero.py export-bibtex > references.bib

# 删除条目（谨慎使用）
python ./scripts/zotero.py delete ITEMKEY123
```

## 详细指南

### Zotero 本地 API 基础

| Endpoint                                | Method | Description                |
| --------------------------------------- | ------ | -------------------------- |
| `/api/items`                            | GET    | List all items (paginated) |
| `/api/items/:itemKey`                   | GET    | Get single item            |
| `/api/items`                            | POST   | Create item(s)             |
| `/api/items/:itemKey`                   | PUT    | Update item                |
| `/api/items/:itemKey`                   | DELETE | Delete item                |
| `/api/collections`                      | GET    | List collections           |
| `/api/collections/:collectionKey/items` | GET    | Items in a collection      |
| `/api/tags`                             | GET    | List all tags              |
| `/api/groups`                           | GET    | List groups                |
| `/api/items/search`                     | POST   | Search items               |
| `/api/items`                            | DELETE | Delete multiple items      |

**Base URL**: `http://127.0.0.1:23119`
**Headers**: `Content-Type: application/json`, `Zotero-API-Version: 3`

> **注意**：响应中的条目包含 `itemKey` 和 `version` 字段。更新（PUT）和删除（DELETE）时必须携带 `version`，以防冲突。

### 操作步骤

1. **前置检查**：运行上面的 `curl` 健康检查。若失败，提醒用户启动 Zotero，并确认已在 Zotero 偏好设置（Advanced → Settings）中勾选 "Enable Local API"。
2. **选择操作**：常用操作走辅助脚本 `./scripts/zotero.py`（见上文命令清单）。
3. **裸 API 调用（高级）**：脚本未覆盖的操作，直接用 `curl` 调用 API。

```bash
# 全文检索条目
curl -s "http://127.0.0.1:23119/api/items?q=quantum&limit=5" | python -m json.tool

# 新建收藏集
curl -s -X POST "http://127.0.0.1:23119/api/collections" \
  -H "Content-Type: application/json" \
  -d '{"name":"My New Collection"}'

# 获取条目总数
curl -s "http://127.0.0.1:23119/api/items?limit=1" | grep -o '"totalResults":[0-9]*'
```

### 错误处理

- **Connection refused**：Zotero 未运行。请用户启动 Zotero。
- **404 Not Found**：item key 或端点无效。
- **409 Conflict**：版本不匹配。重新获取该条目以拿到最新 version 后再更新。
- **Empty results**：检索无匹配结果。尝试更换关键词。

## 注意事项

- Zotero 必须在本机运行，且已在偏好设置中启用本地 API，否则所有请求都会失败。
- 修改（PUT）和删除（DELETE）条目前必须先获取最新的 `version`，否则会收到 409 Conflict。
- 脚本路径相对于 skill 根目录：`./scripts/zotero.py`。
- 删除操作为不可逆，执行 `delete` 前确认 itemKey 无误。
