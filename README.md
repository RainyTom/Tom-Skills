# ~/.agents — Agent Skills 统一真源

合并时间：2026-10-01。本目录是所有 agent skills 的唯一真源（single source of truth），各 agent 的原 skills 路径已改为链接指向这里。

## 真源

- Windows：`C:\Users\24809\.agents\skills\`（11 个 skill，101 个文件）
- WSL：通过 `/mnt/c/Users/24809/.agents/skills` 访问同一真源

## 链接一览

| 环境 | agent | 链接路径 | 类型 | 目标 |
|------|-------|---------|------|------|
| Win | oh-my-pi | `C:\Users\24809\.omp\agent\skills` | Junction | `C:\Users\24809\.agents\skills` |
| Win | GitHub Copilot CLI | `C:\Users\24809\.copilot\skills` | Junction | 同上 |
| WSL | oh-my-pi | `~/.omp/agent/skills` | symlink | `/mnt/c/Users/24809/.agents/skills` |
| WSL | GitHub Copilot CLI | `~/.copilot/skills` | symlink | 同上 |
| WSL | pi（本次新增能力，原本无 skills） | `~/.pi/agent/skills` | symlink | 同上 |

## Skill 清单（11）

oh-my-pi 来源（10）：academic-article-humanizer、academic-paper-analyzer、academic-paper-fetcher、academic-paper-peer-reviewer、alphaxiv、semantic-compression、tool-anything-to-markdown、tool-docx、tool-markdown-translate、zotero-interact

GitHub Copilot CLI 来源（1）：token-efficient

## 新增 skill

直接在 `~/.agents/skills/<skill-name>/` 下新建目录并放入 `SKILL.md`（及相关脚本），所有 agent 立即生效，无需再建链接。

## 回滚

在 git-bash 中运行：

```bash
bash ~/agents-skills-rollback.sh
```

脚本会：拆除全部 Junction/symlink → 把 11 个 skill 移回原路径 → 重建 WSL 侧副本 → 清理空的 `.agents`。

## 备注

- 按用户决定：本次合并未做任何 tar 备份；合并前已验证 WSL 副本与 Win 副本逐字节一致（token-efficient 仅 CRLF/LF 换行符差异），WSL 重复件与 Win 侧 10 个空占位 junction 已直接删除，无信息损失。
- skill 内的 `__pycache__`、`.DS_Store` 为可再生缓存，已随目录原样迁移。
- **Windows 链接是 Junction，不能跨卷；删除链接请用 `rmdir`（或 `cmd /d /c rmdir`），切勿 `rm -rf`——会穿过链接删除真源内容。**
- WSL 链接跨文件系统（/mnt/c），在 WSL 内执行 skill 里的 python 脚本会略慢，属预期现象。
- `.copilot/skills` 下原有的 10 个按 skill 细分的旧 junction（指向 `.omp/agent/skills/<name>`）已拆除，由现在的单链接取代。
