# ~/.agents — Skills / Prompts 统一真源

本目录是所有 agent skills 与 prompts 的唯一真源（single source of truth），同时是一个 git 仓库（remote：`github.com/RainyTom/Tom-Skills`），由 skills-manager 推送备份。

## 目录结构

```
~/.agents/
├── skills/            ← 11 个 skill（唯一真身）
├── prompts/           ← 可复用 prompts（约定见 prompts/README.md）
├── .skill-lock.json   ← vercel skills 维护（首次 skills add -g 后生成；skills-manager 只读）
└── README.md          ← 本文件
```

## 工具链（两者配合）

### 1. vercel skills CLI（安装 / 发现 / 更新 skill）

```bash
skills find [query]                          # 搜索 skills.sh
skills add <repo> -g -a oh-my-pi -a github-copilot -y   # 安装到真源并链接到指定 agent
skills ls -g                                 # 列出已装 skill
skills update -g -y                          # 更新全部
skills remove <name> -g                      # 移除
```

- 安装目标：全局模式写入 `~/.agents/skills`（真源），Windows 下自动用 junction 链接到各 agent 目录，无需管理员权限。
- 它会把本次选择的 agent 记入 `.skill-lock.json` 的 `lastSelectedAgents`。

### 2. skills-manager（备份 / 跨机同步 / 重新分发）

```bash
skills-manager push                # 提交并推送本目录到 GitHub
skills-manager pull                # 新机器上拉取（会自动跑 link）
skills-manager link                # 按 lock/已存配置把 skills 链接到各 agent
```

- 分发目标（本机）：Win Junction → `.omp\agent\skills`（oh-my-pi）、`.copilot\skills`（GitHub Copilot CLI）。
- pi 仅装在 WSL：skills-manager 在 Windows 侧运行检测不到，WSL 的 pi 需另行处理。

## 本地补丁清单（npm 升级会覆盖，需重新打）

| 包 | 文件 | 补丁 |
|---|---|---|
| `@tc9011/skills-manager@0.13.0` | `dist/agents.js` + `dist/agents.d.ts` | 注册表新增 `oh-my-pi`（globalPath `~/.omp/agent/skills`） |
| 同上 | `dist/linker.js` | Windows 下 symlink 改用 junction（修 EPERM，4 处调用点） |
| `skills@1.7.0` | `dist/cli.mjs` | 注册表新增 `oh-my-pi`（约 1918 行） |

上游：`github.com/tc9011/skills-manager`、`github.com/vercel-labs/skills`（其 main 分支已内建 junction 处理）。

## Skill 清单（8）

| 名 | 功能 |
|----|------|
| academic-paper-fetch | 多源下载论文 PDF（arXiv/DBLP/Scholar/Sci-Hub） |
| academic-paper-analyze | 论文批判性深度分析报告 |
| academic-paper-review | 同行审稿意见生成 |
| text-humanize | 去 AI 写作痕迹 |
| documents-to-markdown | 多格式文档转 Markdown |
| alphaxiv-interact | alphaXiv 检索与研究 |
| zotero-interact | Zotero 文献库管理 |
| token-efficient | Copilot token 规则包 |

命名规范：kebab-case；学术工作流三件套以 `academic-` 前缀分组，`-interact` 后缀表示外部服务集成，其余按功能直述。全部 SKILL.md 统一为中文模板（概述/使用场景/使用方法/详细指南/示例/注意事项）。

## 新增 skill / prompt

- skill：放进 `~/.agents/skills/<name>/`（含 `SKILL.md`），跑 `skills-manager link` 分发。
- prompt：放进 `~/.agents/prompts/<name>/PROMPT.md`，见 `prompts/README.md`。
- 完成后 `skills-manager push` 备份。

## 回滚

- 链接问题：重跑 `skills-manager link`（幂等）；拆除单个 agent 的链接用 `rmdir`，**切勿 `rm -rf`**（会穿过 junction 删真源）。
- 完全回滚到合并前：`bash ~/agents-skills-rollback.sh`（注意：它会先拆 `.omp`/`.copilot` 下的 junction，再把 skill 移回原路径）。
