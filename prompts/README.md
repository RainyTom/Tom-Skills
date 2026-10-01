# ~/.agents/prompts

可复用 prompts 的统一存放目录，与 `~/.agents/skills` 平级，随本 git 仓库一起被 skills-manager 备份/同步。

## 约定

- 每个 prompt 一个目录：`<prompt-name>/PROMPT.md`（名称小写字母+连字符）
- `PROMPT.md` 带 YAML frontmatter，字段与 skills 规范一致：

```markdown
---
name: my-prompt
description: 这个 prompt 做什么、什么时候用
---

# 正文（写给 agent 的指令/模板）
```

## 使用方式

各 agent 对 prompt 的加载机制不同，本目录只做**版本管理与同步**，不分发。需要时：
- 手动复制到 agent 的 prompts 目录，或
- 自行建符号链接（Windows 用 junction，见根 README）

新增 prompt：直接在本目录建 `<name>/PROMPT.md`，下次 `skills-manager push` 自动入库。
