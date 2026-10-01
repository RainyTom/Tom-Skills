---
name: alphaxiv
description: '与 alphaXiv 的 MCP 服务器交互的完整指南：在 arXiv 语料中检索论文、深度阅读与分析（AI 结构化报告/全文/按页提取）、探索论文的开源代码仓库、发现与追踪研究者、管理个人论文库。当用户提到 alphaXiv、给出 arXiv 论文 ID 或链接（https://arxiv.org/abs/...、2401.01313 这类格式）、要求查找/总结/分析某篇论文、做文献综述或 related work、追踪某领域最新进展、了解谁在做某个方向、查某位研究者的主页/近况/合作者、管理或收藏论文时，务必使用本技能——即使他们没有明确说出"alphaXiv"。例如"帮我找一下……的论文""这篇论文讲了什么""谁在做 X 方向""把这几篇存到我的库里""从这篇论文提取带页码的实验细节"都属于本技能范围。注意：本技能只处理需要从论文语料获取或整理数据的任务；本地 PDF 转格式、参考文献格式整理、纯知识问答不属于此范围。'
---

# alphaXiv 论文研究助手

通过 alphaXiv 的 MCP 服务器访问 arXiv 论文语料：发现论文、阅读与分析、探索论文代码、追踪研究者、管理论文库。共 18 个工具，分三组：Research（研究）、Researcher（研究者）、Library（图书馆）。当任务需要从论文语料获取或整理数据时使用本技能；本地 PDF 转格式、参考文献格式整理、纯知识问答不属于本技能范围。

## 使用场景

- 按主题查找相关论文（文献发现、related work、领域综述）
- 阅读或总结单篇论文：AI 结构化报告、全文提取、按页引文级问答
- 分析论文的开源代码仓库（超参、数据管线、实现细节）
- 发现某方向的研究者（按发表记录而非自我介绍），查履历/教育/合作者/引用轨迹
- 追踪研究者近况与代表作，关注/取关以订阅其新论文
- 把实验室页面、获奖名单等外部名单解析成 alphaXiv 研究者
- 管理个人论文库：查看/创建/重命名/删除文件夹，存论文、跨文件夹移动、移除

## 使用方法

工具通过 alphaXiv MCP 服务器调用；无 MCP 环境时用 `scripts/alphaxiv.py` 直连。每个工具的完整参数与示例见 `references/tools.md`，拿不准参数时去读，不要靠猜。

按任务快速选型：

| 用户想做什么 | 用哪个工具 |
|---|---|
| 按主题找一批相关论文（文献发现、related work） | `discover_papers` |
| 读整篇论文（AI 结构化报告或全文） | `get_paper_content` |
| 对论文提具体问题，要带页码的引文级内容 | `answer_pdf_queries` |
| 看论文的开源代码仓库 | `read_files_from_github_repository` |
| 找某方向的研究者（按发表记录而非自我介绍） | `find_researchers` |
| 查研究者履历/教育/合作者/论文指标 | `get_researcher` |
| 看某人最近发什么、代表作 | `get_researcher_papers` |
| 把外部名单（实验室页、获奖名单）解析成 alphaXiv 研究者 | `resolve_researchers` |
| 关注/取关研究者（订阅其新论文） | `follow_researcher` / `unfollow_researcher` |
| 查看自己关注了谁 | `list_followed_researchers` |
| 查看自己的收藏文件夹 | `list_library` |
| 存论文/整理论文库 | `save_papers_to_folder` / `create_folder` / `rename_folder` / `move_papers_between_folders` / `remove_papers_from_folder` / `delete_folder` |

## 详细指南

### 前置条件

alphaXiv MCP 服务器必须已配置，否则工具不可用：

- **原生 MCP 客户端**（Claude Code / Cursor / VS Code / Zed 等）：服务器已通过 `claude mcp add --transport http alphaxiv https://api.alphaxiv.org/mcp/v1` 添加，工具直接在工具列表中。首次使用走浏览器 OAuth 授权；脚本/CI 场景可改加 `--header "Authorization: Bearer <key>"`。
- **无 MCP 工具的环境**（纯脚本、CI、无头代理）：用 `scripts/alphaxiv.py` 通过 HTTP 直连端点（需要 API key，在 alphaxiv 网站 Settings > API Keys 创建）。见脚本 `--help`。
- 浏览器内助手（claude.ai 网页等）不支持直接接入（CORS 限制），需本地桥接 `npx mcp-remote https://api.alphaxiv.org/mcp/v1`。

### 核心使用原则

1. **论文 ID 通用**：arXiv ID（`2307.12307`）、arXiv URL、alphaXiv URL、甚至标题，绝大多数工具都接受。回答中引用论文时用 arXiv ID。
2. **批量提问近乎免费**：对同一篇论文的所有问题合并成一次 `answer_pdf_queries` 调用（queries 数组）。要读多篇论文时，对每篇并行发一次调用。
3. **引文必须带页码**：`answer_pdf_queries` 返回 XML `<paper id="..."><page num="N">...</page></paper>`，直接把对应页文本用于构造引用，不要凭记忆编页码。
4. **难度与时间窗**：`discover_papers` 的 `difficulty`（1-10）控制检索努力度，广泛综述调高、快速找几篇调低。`published_after`/`published_before` 只在用户明确给出时间边界时才填——填了会硬性排除范围外论文。
5. **注意配额**：Research 组与研究者搜索/档案工具会消耗助手配额（assistant quota）；follow/unfollow 与图书馆工具不消耗。
6. **破坏性操作前确认**：`remove_papers_from_folder`、`move_papers_between_folders`、`delete_folder`、`unfollow_researcher` 会改动用户数据，先向用户说明将发生什么再执行。

### 参数陷阱速查（真实踩过的坑）

以下参数名/取值错误会被服务端直接拒绝（-32602）或静默忽略，每次重试都浪费配额和时间。拿不准就查 `references/tools.md` 的参数表，不要靠猜：

- `discover_papers`：`prioritize` 只接受 `"default" | "historical" | "recency"`。**官方文档示例里的 `"relevance"` 是错的，会被服务端拒绝**。
- `find_researchers`：主题检索必须用 `topic` 参数；传 `question` 会被静默忽略（返回全局引用排名，看似成功实则答非所问）。
- `get_paper_content`：参数名是 `url`，不是 `paper`/`paper_id`。
- `read_files_from_github_repository`：参数名是 `githubUrl` 和 `path`。
- 数量上限（为拿全结果反复调用前先确认）：`get_researcher_papers` 每人最多 10 篇；`get_researcher` 一次最多 25 人；`resolve_researchers` 一次最多 50 人；`save_papers_to_folder`/`remove_papers_from_folder`/`move_papers_between_folders` 每次 1-50 篇；`find_researchers` 用 `limit` 分页（默认 12）。

### 标准工作流

#### 文献综述

1. `discover_papers` 找候选（3-4 个关键词 + 语义化 question）。
2. 换关键词/提高 difficulty 再跑 1-2 次，补齐盲区。
3. 对每篇论文用 `answer_pdf_queries` 批量提取：核心方法、数据集、评测基准、局限。
4. 汇总成结构化综述报告（见"输出格式"）。

#### 深度读论文 / 论文问答

1. 用户给 ID/URL/标题即可定位，无需先检索。
2. 常规问题优先 `get_paper_content`（默认返回 AI 结构化报告，专为 LLM 消费优化）；报告不满足时设 `fullText: true` 拿原始全文。
3. 需要引文级证据或细节问题时用 `answer_pdf_queries`，一次调用批量问完。
4. 结合 `read_files_from_github_repository` 核对实现细节（超参、数据管线）。

#### 论文代码分析

1. `discover_papers` 或已知论文 → 从结果/元数据拿到 GitHub URL。
2. `read_files_from_github_repository` 传 `path: "/"` 看完整文件树与顶层文件。
3. 再深入具体目录/文件（读目录会并行抓取全部文件）。

#### 研究者发现与追踪

1. `find_researchers` 按主题找（从作者署名图匹配，比简历文本可靠）；`topic_authors: "senior"` 找 PI、`"lead"` 找学生/博后。
2. `get_researcher` 看履历、教育、合作者、引用轨迹（`include` 按需选）。
3. `get_researcher_papers` 用 `sort: "recent"` + `published_after` 看近况，`"cited"` 看代表作。
4. 用户想持续跟进 → `follow_researcher`（slug 用返回的 `[SLUG=...]` 或 `/@slug`）。
5. 外部名单（实验室页等）→ `resolve_researchers` 一次性批量解析成当前任职。

#### 论文库管理

1. `list_library` 是入口——所有库工具都依赖它返回的 `folder_id`（不透明 ID，每次使用前先查）。
2. 默认三个阅读状态文件夹（Want to read / Reading / Completed）互相独立，一篇论文可同时在多个文件夹。
3. 默认文件夹与 publications/private-papers 文件夹不可重命名/删除。
4. `save_papers_to_folder` 幂等、默认存进 "Want to read"；`move_papers_between_folders` 原子移动，目标已存在则报告重复并保留在源。

### 输出格式

**简单问答**：直接在对话中回答。引用格式 `[论文ID/标题，第 N 页]`，基于 `answer_pdf_queries` 返回的实际页码。回答完主动问是否要存入其论文库。

**系统性任务**（综述、深度调研、研究者报告）：输出结构化 Markdown 报告并保存为文件，按此模板：

```markdown
# [标题]
## 概述
（背景与范围，1-3 段）
## 关键发现 / 论文
（每条含：标题、arXiv ID、发表时间、机构、核心方法、关键数据集/基准）
## 综合分析
（跨论文的模式、分歧、空白）
## 引用列表
（完整 arXiv ID 列表）
```

报告中每条论文信息都来自工具返回结果，不编造不存在的论文、数字或结论。

### 无 MCP 环境（脚本方式）

只有原生 MCP 工具不可用时才走这条路：

```bash
export ALPHAXIV_API_KEY=<你的key>
python scripts/alphaxiv.py list-tools
python scripts/alphaxiv.py call discover_papers '{"keywords": ["hallucination","LLM"], "question": "...", "difficulty": 5}'
```

完整用法见 `references/tools.md` 末尾与脚本 `--help`。

## 注意事项

- 参数名/枚举值拿不准时查 `references/tools.md` 的参数表，错误参数会被拒绝（-32602）或静默忽略，重试浪费配额。
- Research 组与研究者搜索/档案工具消耗助手配额；follow/unfollow 与图书馆工具不消耗。
- `published_after`/`published_before` 只在用户明确给出时间边界时填，填了会硬性排除范围外论文。
- 破坏性操作（`remove_papers_from_folder`、`move_papers_between_folders`、`delete_folder`、`unfollow_researcher`）执行前先向用户说明将发生什么。
- 默认文件夹与 publications/private-papers 文件夹不可重命名/删除。
- 引用必须基于 `answer_pdf_queries` 返回的实际页码，不要凭记忆编页码。
