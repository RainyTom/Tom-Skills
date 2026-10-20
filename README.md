# Tom-Skills

个人 Agent Skills 单一真源库。各 agent 通过 junction 链接引用本仓库 `skills/` 下的 skill。

## 真源与链接结构

- **真源**：`~/.agents/skills/`（本目录），新增/改名/删除 skill 只动这里
- **链接**：各 agent 的 skills 目录下是每个 skill 的 junction（Windows 目录联接），指向 `~/.agents/skills/<name>`
- 已链接 agent（9）：

| agent | 链接位置 |
|-------|---------|
| oh-my-pi | `~/.omp/agent/skills` |
| GitHub Copilot CLI | `~/.copilot/skills` |
| Antigravity | `~/.gemini/antigravity/skills` |
| Codex | `~/.codex/skills` |
| Cursor | `~/.cursor/skills` |
| 通用（Amp/Replit/Kimi 等） | `~/.config/agents/skills` |
| OpenCode | `~/.config/opencode/skills` |
| Firebender | `~/.firebender/skills` |
| Deep Agents | `~/.deepagents/agent/skills` |

链接由 `@tc9011/skills-manager` 维护（上游 `github.com/tc9011/skills-manager`），重建命令：

```bash
skills-manager link --agents oh-my-pi github-copilot antigravity codex cursor universal opencode firebender deepagents
```

## WSL 同步

WSL（`~` = `/home/yiming`）内的 agent 同样链接到本仓库真源，不另建副本：

- `~/.agents` 是指向本仓库（`/mnt/c/Users/24809/.agents`）的符号链接，真源唯一
- WSL 内独立安装了一份 skills-manager（nvm node 的全局 npm 包），Linux 下自动用真符号链接（非 junction）
- 已链接 WSL agent（3）：oh-my-pi（`~/.omp/agent/skills`）、github-copilot（`~/.copilot/skills`）、universal（`~/.config/agents/skills`）

WSL 侧重链命令：

```bash
skills-manager link --agents oh-my-pi github-copilot universal
```

注意：npm 版 `skills-manager@0.13.0` 上游**不含 `oh-my-pi`**，WSL 这份和 Windows 那份一样打了本地补丁（`dist/agents.js` 中 `pi` 条目后追加 oh-my-pi 条目），升级 npm 包后需重新打补丁。

## Skill 清单（10）

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
| archify | 架构/流程/时序图生成（经 skills.sh 安装，装前请审阅） |
| archify-review | archify 变更评审（经 skills.sh 安装，装前请审阅） |

命名规范：kebab-case；学术工作流三件套以 `academic-` 前缀分组，外部服务集成为 `<service>-interact`，其余按功能直述。SKILL.md 统一为中文模板（概述/使用场景/使用方法/详细指南/示例/注意事项）。

## 维护须知

1. **`npx skills add` 会破坏链接**：vercel skills CLI 向各 agent 目录"copy"时会先删除 junction、落成实体副本，导致 skill 更新不再同步。用它装完 skill 后，重跑上面的 `skills-manager link` 命令修复（它会清掉实体副本重建 junction）。
2. **PromptScript 报错正常**：`PromptScript does not support global skill installation` 可忽略。
3. **npm 升级 skills-manager 后**需重打本地补丁（Windows junction 支持；本仓库 `.gitignore` 亦有配套追加）。
4. **新增 skill**：直接在 `~/.agents/skills/<name>/` 建目录放 SKILL.md，然后重跑 link 命令。
5. **安全**：skill 以 agent 全权限运行；装第三方 skill 前先看内容（`archify` 在 Socket 有 2 条告警、`archify-review` Snyk 中风险，详见 https://skills.sh/tt-a1i/archify）。
6. **回滚**：早期合并的回滚脚本在 `~/agents-skills-rollback.sh`；本仓库自身的历史版本在 git 备份提交中（`git log --oneline`）。
