---
name: token-efficient
description: "Token 效率规则包——快速入口，列出各任务场景的规则配置档，并概述核心约束。"
user-invocable: true
---

# Token-efficient（skill 入口）

本 skill 汇集 token 高效的提示词配置档。在交互会话中使用本 skill，可列出或手动加载这些配置档。

- 核心规则：见 `token-efficient.instructions.md`（全局指令，自动加载）。
- 本目录下的配置档文件：`COPILOT.coding.md`、`COPILOT.agents.md`、`COPILOT.analysis.md`、`COPILOT.benchmark.md`。

## 快速命令

在对话中说以下任一语句，即可加载对应配置档：

| 这样说 | 效果 |
|----------|-------------|
| "Use coding profile" | 加载 `COPILOT.coding.md` |
| "Use agents profile" | 加载 `COPILOT.agents.md` |
| "Use analysis profile" | 加载 `COPILOT.analysis.md` |
| "Use benchmark profile" | 加载 `COPILOT.benchmark.md` |
| "Load all rules" | 加载完整规则集 |
| `/token-efficient` | 调用本 skill（若 UI 支持斜杠命令） |

也可以组合使用："analysis profile for this data, but use coding rules for the code part."

## 来源

配置文件镜像自 `copilot-token-efficient/profiles/`。修改后请从项目复制回去以保持同步。
