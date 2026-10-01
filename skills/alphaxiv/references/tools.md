# alphaXiv MCP 工具完整参考

端点：`https://api.alphaxiv.org/mcp/v1`（Streamable HTTP，MCP v1.0.0）
认证：OAuth 2.1（浏览器交互）或 `Authorization: Bearer <API key>`（无头/脚本）。

## Research 组（消耗助手配额）

### discover_papers
主题检索，内部跑 agentic 检索循环（关键词 + 向量 + 可选多轮追问）。文献发现、related work、广覆盖检索的首选。

参数：
- `keywords` (string[], 必填)：3-4 个简洁关键词，用于精确名称/缩写/方法/基准/作者/标题匹配。纯文本。
- `question` (string, 必填)：详细的语义描述——这篇论文应该回答用户什么需求，包含重要概念、方法、应用、相关术语。
- `difficulty` (number 1-10, 必填)：检索努力量估计。越高越慢但会触发多轮追问检索。
- `published_after` (string, 可选)：只返回该日期（YYYY-MM-DD）及之后首次发表的论文。**用户没给时间边界就别填**——填了会硬性排除。
- `published_before` (string, 可选)：同理，历史窗口上限。
- `prioritize` ("default"|"historical"|"recency", 可选)：排序优先级。**注意：官方文档示例中的 "relevance" 是非法值，服务端会拒绝（-32602）**。

返回：5-15 篇排名论文，含标题、发表日期、贡献机构、摘要预览、arXiv ID。

示例：
```json
{"keywords": ["hallucination", "LLM", "factuality"],
 "question": "Recent approaches to reducing hallucination in large language models, covering retrieval grounding, decoding-time interventions, and post-hoc verification.",
 "difficulty": 5, "prioritize": "relevance"}
```

### get_paper_content
获取论文文本。默认返回 AI 生成的结构化中间报告（为 LLM 消费优化）；无报告时自动回退到全文提取；`fullText: true` 跳过报告直接拿原始提取文本（逐页）。

参数：
- `url` (URL, 必填)：arXiv 或 alphaXiv URL（`https://arxiv.org/abs/2307.12307`、`https://arxiv.org/pdf/2401.12345`、`https://www.alphaxiv.org/abs/2307.12307`）。
- `fullText` (boolean, 可选，默认 false)：true 时返回逐页原始提取文本。

### answer_pdf_queries
返回单篇 PDF 中与查询相关的**过滤后逐页内容**。输出 XML：`<paper id="..."><page num="N">page text</page>...</paper>`，可直接用页文本构造引用。

参数：
- `paper` (string, 必填)：论文 ID（`2307.12307`）、URL 或标题。支持 arXiv（pdf/abs）、alphaXiv（alphaxiv.org/abs/*）、Semantic Scholar 摘要页、直接 PDF URL。标题会解析为单一最佳匹配并在 `<paper>` 标签中回报。
- `queries` (string[], 必填)：一个或多个对所需信息点的简要描述。

原则：
- 同一论文的所有问题合并进一次调用（多次查询几乎免费）。
- 读多篇论文 → 每篇一次调用、并行发出。
- 用返回页文本直接构造引用（页码以 `num` 为准）。

### read_files_from_github_repository
读取论文 GitHub 仓库文件。专门为高效代码探索设计。

参数：
- `githubUrl` (URL, 必填)：仓库 URL，如 `https://github.com/openai/gpt-2`。
- `path` (string, 必填)：文件或目录路径。**`/` 返回完整文件树 + 全部顶层文件**；目录会并行抓取其中所有文件；文件返回其内容。

## Researcher 组

研究者以 `/@slug` 地址的 slug 标识；`get_researcher`、`get_researcher_papers`、`resolve_researchers` 也接受普通姓名并自动解析（容忍拼写错误）。搜索与档案工具消耗配额；follow 工具不消耗。

### find_researchers
按主题/机构/履历/合著关系找研究者。主题查询从**作者署名图**回答（而非简历文本），因此能找到"实际在发该方向论文的人"。可组合当前任职、角色、引用区间、带日期的工作经历过滤。

参数（全部可选，除组合需要）：
- `query` (string)：任务是识别某人时填姓名；否则可省略。
- `topic` (string)：研究主题（"谁在做 X"）。**用该领域论文自己的用词，一个概念**；把相关概念拼起来反而一个都匹配不到。
- `topic_authors` ("lead"|"senior"|"any")：按作者位加权——lead 是学生/博后（驱动工作的人），senior 是收尾的 PI。默认 lead。
- `affiliation` (string)：当前机构。写常用名即可，会匹配所有索引拼写。
- `include_past_affiliations` (boolean, 默认 false)：简写"在该机构的过往职位"，排除当前仍在该机构的。
- `position` (object)：履历过滤。affiliation、role、status、各日期边界作用于**同一职位行**。
- `relationship` (object)：针对锚定研究者的合著证据：共享论文数、占对方全部产出比例、其领衔频率。
- `role` (string)：当前角色，token 匹配（'professor' 匹配助理/副教授）。
- `min_citations` / `max_citations` (number)：引用上下限，前者筛资深、后者找新星。
- `sort` ("relevance"|"citations"|"recent_activity"|"relationship_strength")：排序；主题检索自带排序、忽略此项。默认 relevance。
- `limit` (1-100)：每页条数，默认 12（关系检索默认 50）。
- `page` (number)：分页，从 1 起。

返回：排名研究者，带 `[SLUG=...]` 句柄、姓名、当前职位、引用数、匹配依据。主题检索还返回该主题的代表论文及作者。

### get_researcher
一次获取最多 25 位研究者的紧凑档案。姓名自动解析、容忍拼写错误，无需 slug。默认返回当前职位 + 最多 5 个精选过往职位；其余全为 opt-in。

参数：
- `researchers` (string[], 1-25, 必填)：全名或精确 slug；纠错会在内联回报。
- `include` (string[])：额外章节：bio、position_history、linkedin_experience、education、citation_trajectory、coauthors、alphaxiv_account、links。
- `papers` ("none"|"notable"|"recent", 默认 none)：附带论文上下文；大批量/带日期的问题改用 get_researcher_papers。
- `paper_limit` (1-10)：设置 papers 时每人论文数，默认 3。

### get_researcher_papers
一位或多位研究者在 alphaXiv 上的论文，按人分组。`sort: "recent"` + `published_after` 回答"现在在做什么"；`"cited"` 找代表作。返回的论文 ID 可直接接入论文工具。

参数：
- `researchers` (string[], 1-25, 必填)：全名或精确 slug，解析方式同 get_researcher。
- `sort` ("recent"|"cited"|"viewed")：cited=代表作、recent=当前活动、viewed=alphaXiv 关注度。默认 cited。
- `published_after` (string, YYYY-MM-DD)。
- `limit_per_researcher` (1-25)：每人论文数，默认 10。

### resolve_researchers
把外部来源的人名列表（实验室花名册、团队页、获奖名单）解析为当前 alphaXiv 研究者条目，以便引用"现在任职"而非页面所写。一次性传所有人。

参数：
- `people` (object[], 1-50, 必填)：每项为姓名（按来源原样）+ 可选个人/机构/Scholar/LinkedIn/OpenReview URL。**不要传共享的花名册 URL**。
- `related_researchers` (string[], 最多 5)：与整个列表相关的人名/slug，仅用于消歧（合著证据），不作为来源所声称关系的证明。

### list_followed_researchers
列出用户关注的研究者（slug、姓名、当前头衔/机构、引用数）。关注后其新论文会进入用户的 alphaXiv 信息流。无参数。

### follow_researcher
关注研究者（写操作，幂等）。slug 来自 find_researchers、get_researcher 或 `/@slug` 档案 URL。
参数：`slug` (string, 必填)。

### unfollow_researcher
取关研究者（破坏性，幂等）。slug 来自 list_followed_researchers。
参数：`slug` (string, 必填)。

## Library 组

文件夹用 `list_library` 返回的**不透明 folder_id** 寻址。默认 'Want to read'、'Reading'、'Completed' 表示阅读状态，互相自由重叠——一篇论文可同时在任意多个文件夹。

### list_library
列出用户的文件夹（bookmark 集合）：folder_id、名称、类型、parent_id、共享状态、论文数。**其他所有库工具的人口**。

参数：
- `include_papers` (boolean, 默认 false)：同时列出每个文件夹内的论文（每夹封顶）。
- `paper_ids_or_urls` (string[])：报告这些论文已存在于哪些文件夹。

返回：文件夹列表；带 include_papers 时每夹带论文；带 paper_ids_or_urls 时附加 paper_membership 节，映射每篇论文到其所在文件夹。

### save_papers_to_folder
把论文加入文件夹（写操作）。未入库的论文会从 arXiv 拉取。幂等，绝不从其他文件夹移除论文。
参数：
- `paper_ids_or_urls` (string[], 1-50, 必填)：arXiv ID 或 alphaXiv/arXiv URL。
- `folder_id` (string, 可选)：目标文件夹，默认 "Want to read"。

### remove_papers_from_folder
从单个文件夹移除论文（破坏性）。只影响该文件夹，其他文件夹中的成员关系不受影响。
参数：
- `paper_ids_or_urls` (string[], 1-50, 必填)。
- `folder_id` (string, 必填)。

### move_papers_between_folders
把论文从源文件夹移到目标文件夹（破坏性，原子操作）：先加入目标、再从源移除。已在目标的论文报告为重复并**留在源文件夹**。
参数：
- `paper_ids_or_urls` (string[], 1-50, 必填)。
- `from_folder_id` (string, 必填)。
- `to_folder_id` (string, 必填)。

### create_folder
创建自定义文件夹，可嵌套（写操作）。
参数：
- `name` (string, 1-100, 必填)。
- `parent_folder_id` (string, 可选)：嵌套到该已有文件夹下。

### rename_folder
重命名自定义文件夹（写操作）。**只有自定义文件夹可重命名**，默认阅读状态文件夹与 publications 文件夹不行。
参数：
- `folder_id` (string, 必填)。
- `name` (string, 1-100, 必填)。

### delete_folder
删除文件夹及其论文成员关系（破坏性）。论文本身不删除；publications 与 private-papers 文件夹不可删除。
参数：`folder_id` (string, 必填)。

## 无 MCP 环境：scripts/alphaxiv.py

原生 MCP 工具不可用时的 HTTP 直连方式。需要 API key（Settings > API Keys 创建）。

```bash
export ALPHAXIV_API_KEY=sk-...
python scripts/alphaxiv.py list-tools
python scripts/alphaxiv.py call <tool_name> '<json arguments>'
python scripts/alphaxiv.py call discover_papers '{"keywords": ["RAG"], "question": "...", "difficulty": 3}'
```

返回 JSON（MCP tool result）。凭据也可用 `--api-key` 传入或从 `~/.config/alphaxiv/key` 读取。
