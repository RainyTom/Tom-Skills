---
name: token-efficient
user-invocable: true
description: Token-efficient rules bundle — quick entry to per-task profiles and a short summary of core constraints.
---

# Token-efficient (skills entry)

This skill groups token-efficient prompting profiles. Use the skill to list or manually load profiles in interactive sessions.

- Core rules: see `token-efficient.instructions.md` (global instructions, auto-loaded).
- Profile files in this folder: `COPILOT.coding.md`, `COPILOT.agents.md`, `COPILOT.analysis.md`, `COPILOT.benchmark.md`.

## Quick commands

Say any of the following in chat to load a specific profile:

| Say this | What happens |
|----------|-------------|
| "Use coding profile" | Loads `COPILOT.coding.md` |
| "Use agents profile" | Loads `COPILOT.agents.md` |
| "Use analysis profile" | Loads `COPILOT.analysis.md` |
| "Use benchmark profile" | Loads `COPILOT.benchmark.md` |
| "Load all rules" | Loads the full ruleset |
| `/token-efficient` | Invokes this skill (if UI supports slash commands) |

You can also combine: "analysis profile for this data, but use coding rules for the code part."

## Source

Profile files are mirrored from `copilot-token-efficient/profiles/`. Keep them in sync by copying back from the project when changed.

