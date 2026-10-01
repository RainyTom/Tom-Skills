---
name: academic-paper-fetch
description: "通过标题、arXiv ID 或 DOI 下载论文 PDF，支持 arXiv / DBLP / Google Scholar / Sci-Hub 多源获取，自动去重检查。仅处理物料获取阶段，不进行格式转换或内容分析。"
argument-hint: "论文标题、arXiv ID、DOI、doi.org 链接或下载 URL"
---

# 论文 PDF 下载

下载论文全文 PDF 并输出元数据 JSON。输入可以是论文标题、arXiv ID、DOI、doi.org 链接或下载 URL。当需要获取论文物料（后续交给其他技能做格式转换或内容分析）时使用本技能。

## 使用场景

- 用户提供论文标题、arXiv ID 或 DOI，需要拿到 PDF 全文
- 用户提供 doi.org 链接或下载 URL，需要下载并落盘
- 需要为新论文建立 PDF + 元数据档案，先查重再获取

## 使用方法

提供论文标题、arXiv ID、DOI、doi.org 链接或下载 URL，并指定输出目录，按下方工作流程依次执行。

## 详细指南

### 目标制品

- **PDF 文件** — 下载的论文全文（文件名为标题的下划线化形式）
- **元数据 JSON 文件** — 包含 title、main_tag、tags、doi/arxiv_id 等字段

> 注意：输出路径由用户指定，PDF 与元数据放入同一目录。后续由 `pdf-conversion` 技能进行格式转换。

### 工作流程

#### 步骤 1：去重检查

- **输入**：论文标题 / DOI / arXiv ID。
- **操作**：在用户指定的目标位置搜索已有 PDF 或元数据文件匹配。
- **输出**：`"existing"` 或 `"new"` 决策。若为 `"existing"`，停止流程并报告路径。

#### 步骤 2：路径决策

- **输入**：论文问题定义与方法族。
- **操作**：与用户协商确定 `main_tag`（问题类型/方法族）和输出路径。
- **输出**：确定的 `main_tag` 与输出路径（目标目录由用户指定）。

#### 步骤 3：PDF 获取

- **输入**：来源 URL / arXiv ID / DOI。
- **操作**：依次尝试以下来源，取第一个成功结果：
  1. arXiv：[`./scripts/fetch_from_arxiv.py`](./scripts/fetch_from_arxiv.py)
  2. DBLP：[`./scripts/fetch_from_dblp.py`](./scripts/fetch_from_dblp.py)
  3. Google Scholar：[`./scripts/fetch_from_google_scholar.py`](./scripts/fetch_from_google_scholar.py)
  4. DOI / Sci-Hub：使用 DOI（支持 `doi.org` 前缀）构造 `https://www.sci-hub.su/<DOI>` 并下载 PDF（若可访问）
- **输出**：PDF 文件下载至用户指定的输出路径，存在且大小 > 0。若所有来源失败，报告失败原因并终止。

#### 步骤 4：输出元数据并移交

- **输入**：下载成功的 PDF 文件路径与提取的元数据。
- **操作**：
  1. 在 PDF 同目录下写入 `<filename>.meta.json`（包含 title、main_tag、tags 等字段）。
  2. 向用户报告下载完成。

### 错误处理

| 失败场景                       | 行为                                           |
| ------------------------------ | ---------------------------------------------- |
| PDF 获取失败（所有来源均失败） | 报告失败来源，终止流程，不写入文件             |
| 去重命中（已存在）             | 报告"existing"及已有路径，停止流程（不覆盖）   |
| Sci-Hub 未命中或不可访问       | 记录该来源失败，继续其他来源或给出手动下载建议 |
| meta.json 写入失败             | 记录警告，不阻塞主流程，但需手动补写           |

## 注意事项

- 仅处理物料获取阶段，不进行格式转换或内容分析。
- 所有来源失败时不得写入任何文件。
- 去重命中时不得覆盖已有文件。
