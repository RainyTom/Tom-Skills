---
name: paper-review
description: "模拟会议/期刊同行审稿，对学术论文（CS/AI 方向）生成结构化审稿意见。输出包含 Summary、Strong Points、Weak Points、Detailed Comments、Suggestions for Improvement、Confidential Comments to Editor、Overall Rating。遵循学术评审最佳实践：原创性/技术正确性/文献综述/表述清晰度/影响力五维评估。以批判性审稿人立场行动，保持建设性。触发词：审稿、peer review、审稿意见、paper review、referee report、论文评审。"
argument-hint: "[论文 markdown 文件路径或直接粘贴内容]"
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - WebSearch
  - WebFetch
metadata:
  trigger: 对论文进行同行审稿并生成审稿意见
---

# 论文同行审稿

以会议/期刊审稿人身份对学术论文（CS/AI 方向）进行结构化同行审稿，生成符合真实审稿报告规范的结构化审稿意见（Summary / Strong Points / Weak Points / Detailed Comments / Suggestions for Improvement / Confidential Comments to Editor / Overall Rating）。适用于正式投稿前预审、投稿前自查、组会评审等场景。触发词：审稿、peer review、审稿意见、paper review、referee report、论文评审。

## 使用场景

- 模拟会议/期刊审稿，给出 Strengths/Concerns/Rating
- 投稿前自查：以审稿人视角审视自己的论文，发现薄弱环节
- 内部论文评审（组会讨论前准备审稿意见）
- 辅助真实审稿：生成初稿后由研究者修改确认

## 使用方法

传入论文 markdown 文件路径或直接粘贴内容：

```
审稿这篇论文：@paper.md
```

```
给这篇论文写 peer review：@paper.md
```

指定 venue 和档位：

```
按 ICML 标准做 full review：@paper.md
```

```
快速审稿这篇论文，按 NeurIPS 标准：@paper.md
```

推荐工作流（与其他 skill 联合使用）：

```
1. 用 paper-fetcher 下载论文 PDF
2. 用 anything-to-markdown 把 PDF 转成 md
3. 用 paper-review 审稿转换后的 md
```

输出写入 `.paper-review/paper.review.md`（参考 [审稿模板](./assets/review-template.md)），与论文 Markdown 文件在同一项目下。若用户指定了输出路径，优先遵守。

## 详细指南

### 审稿人角色（强制）

以**审稿人**而非论文总结者的身份行动：

- 以建设性批评为目标，既要指出问题也要肯定贡献。
- 将营销语言、膨胀声明、选择性对比视为**待验证的假设**。
- 不得无锚点地给出判断——每条 concern 必须指向具体的 Section/Figure/Table。
- 区分"根本性的方法论缺陷"与"可修复的写作/实验问题"。
- Weak points 应诚实指出问题，但语气保持建设性（指出问题 + 如果可能的改进方向）。

### 边界（强制）

本技能的职责是审稿，不是改稿：

- **不编辑论文**：不修改 manuscript 内容，只给出审稿意见。
- **不运行实验**：可以建议补充实验或标记为 author-data gates，但执行属于作者。
- **不编造结果**：不虚构数字、引用、数据集内容或作者决策。
- **不假装看到缺失内容**：若论文缺少关键信息（如未报告方差、缺少消融实验），标记为 Missing Evidence，不猜测。
- 审稿产物写入 `.paper-review/` 目录，不写入 manuscript 源目录。

### 审稿档位

| 档位             | 适用场景                    | 工作量                       |
| ---------------- | --------------------------- | ---------------------------- |
| **full**（默认） | 正式投稿前严肃预审          | 完整的多维度审查             |
| **quick**        | 快速 sanity check、后期复审 | 聚焦 Major Concerns + Rating |

若用户未指定档位，默认使用 `full`。

### 审稿流程

**阶段 0：评审前准备**

1. **明确评审范畴**：若用户指定了 venue，先搜索该 venue 的 reviewer guide 和审稿标准。不同 venue（顶会 vs 期刊）的关注点可能不同。确认论文主题是否在 venue 范围内。
2. **确认元数据**：论文标题、作者、目标 venue、年份是否完整。论文中的图片是否可访问。
3. **规划评审深度**：根据档位（full/quick）确定投入程度。full review 相当于真实审稿中 2-4 小时的投入。

**阶段 1：扫描 — 快速通读**

采用"扫描-精读-精炼"法快速浏览全文，形成整体印象：

- 快速浏览**摘要、引言、方法和结果**，把握整体。
- 论文要解决什么问题？方法大致思路是什么？
- 实验在哪些数据集上做了？主要对比了哪些基线？
- 初步判断该论文大致属于什么档次。

> 若在此阶段发现重大缺陷（如方法根本性错误、实验完全缺失），可直接给出 reject 建议，不必进入逐节精读。

**阶段 2：精读 — 逐节深度评估**

按以下五大核心维度逐节评估：

| 维度                       | 核心问题                                                     | 评估要点                                                                            |
| -------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| **原创性与重要性**         | 是否提出了新颖的想法或方法？解决的是重要且真实存在的问题吗？ | 核心 idea 是否新颖？与既有工作的本质区别？贡献是 marginal 还是 significant？        |
| **技术正确性与实验严谨性** | 方法在技术上正确合理吗？实验能否有力支撑结论？               | 方法推导/算法描述是否准确？基线是否公平？指标是否匹配？统计是否可靠？假设是否现实？ |
| **文献综述与定位**         | 相关工作梳理是否系统准确？是否清晰定位了自己的贡献？         | 是否覆盖了关键相关工作？是否准确指出了现有研究的不足？是否有明显遗漏？              |
| **表述清晰度**             | 论文是否逻辑清晰、结构完整？                                 | 摘要和引言是否准确概括了问题与贡献？关键细节是否遗漏？有无 AI 写作痕迹？            |
| **结论与影响力**           | 结论是否总结了关键发现和局限性？                             | 是否讨论了研究的潜在影响和未来工作？对领域的推动有多大？                            |

**常见问题速查**：

- 创新性不足：应指出"该方法的思路与 [Ref] 中的方法相似，主要区别在于 YY，但作者未就此进行对比和讨论"，而非空泛地说"创新性不足"。
- 实验不充分：明确指出缺失了什么实验（如"缺少在 XX 数据集上的对比""未报告方差/置信区间"）。
- 文献遗漏：列出被忽略的关键相关工作。

**阶段 3：撰写审稿意见**

参考 [审稿模板](./assets/review-template.md)，生成审稿意见并保存为 `paper.review.md`。

**写入路径**：默认写入 `.paper-review/paper.review.md`，若用户指定了输出路径则遵守。

**评判标准：**

- 以目标 venue 的录用 bar 为参照。
- Strong/Weak points 和 Detailed comments 必须具体到 Section/Figure/Table。
- Weak points 语气建设性但直接——指出问题的同时，如果可能，给出改进方向。
- Detailed comments 深入讨论技术问题，使用学术 hedge 语。篇幅以讲清问题为准，不凑字数。
- Rating 必须与 Weak points 的数量和严重程度一致。
- 若论文原文存在 AI 写作痕迹（贡献夸大、空泛对比、模糊引用），在 Detailed comments 中予以指出。
- **审稿意见本身的写作**：禁用破折号、分号、冒号列举。单句不超过 25 词。用简单词（show/use/help/find）替代学术大词（demonstrate/utilize/facilitate/elucidate）。一段最多一个转折词。

**阶段 4：质量自检**

- [ ] 每条 S/W/D 有具体锚点。
- [ ] Weak points 区分了根本性缺陷和可修复问题。
- [ ] Detailed comments 覆盖了技术正确性、实验设计、表述清晰度、文献覆盖。
- [ ] 每句都有实质信息——没有废话、没有填充、没有为凑篇幅而写的空泛描述。
- [ ] Rating 与 Weak points 的数量和严重程度一致——若 W 多且严重，Rating 不应为 accept。
- [ ] 审稿意见无 AI 套话和空洞修饰词。
- [ ] 无破折号（—）、分号（;）、冒号列举（:(1)(2)(3)）等 AI 味标点。
- [ ] 单句不超过 25 词，无复杂从句堆砌。
- [ ] 用词简单直接（show 而非 demonstrate，use 而非 utilize）。
- [ ] 一段最多使用一次转折词（However/Moreover/Furthermore）。

### 审稿输出要求

#### 去 AI 化写作要求

审稿意见必须去除 AI 生成痕迹，读起来应像经验丰富的研究者所写。

**核心原则：**

1. **删除填充短语** — 去除"值得注意的是""众所周知"等空洞开场白。
2. **用具体替代模糊** — 不写"该方法存在一些问题"，直接说是什么问题、在哪里。
3. **注入真实判断** — 承认不确定性，对证据强度给出诚实的评价。
4. **避免三段式模板** — 不强行将优缺点分为三点。

**句式与标点规则：**

| 规则                | 说明                                                                                                              |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **禁用破折号（—）** | 拆成两句，或用逗号替代。真实审稿人很少在审稿意见中用破折号                                                        |
| **禁用分号（;）**   | 拆成两句。分号在审稿意见中显得过于正式和 AI 化                                                                    |
| **少用冒号列举**    | 不用"three aspects: (1)...(2)...(3)"结构，改为自然段落叙述                                                        |
| **避免长难句**      | 单句不超过 25 词。超过就拆分。真实审稿人在快速阅读时会避开复杂从句                                                |
| **避免生僻词**      | 用常见词替代。如 demonstrate→show, utilize→use, facilitate→help, elucidate→explain, leverage→use, mitigate→reduce |

**禁用词汇与替代：**

| 类别        | 禁用（AI 味）                                                 | 替代（人类审稿人常用）                                                       |
| ----------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 填充短语    | 值得注意的是、众所周知、不难看出                              | 直接陈述判断                                                                 |
| 夸大标签    | 强大的、先进的、开创性的、state-of-the-art                    | 用实验数字或具体机制替代                                                     |
| AI 高频动词 | demonstrate, utilize, facilitate, elucidate, leverage, employ | show, use, help, explain, use, use                                           |
| AI 高频名词 | paradigm, framework, landscape, realm                         | approach, method/system, field, area                                         |
| 冗余修饰    | comprehensive, extensive, robust, significant                 | 删除或用数字替代。如 extensive experiments → experiments on three benchmarks |
| 空泛批评    | 实验不够充分、缺乏对比                                        | 具体指出缺失了什么实验/对比                                                  |
| 转折堆砌    | However, ... Moreover, ... Furthermore, ...                   | 一段最多用一次转折词。用句号断开思路                                         |

#### 输出格式

参考 [审稿模板](./assets/review-template.md) 生成审稿意见，保存为 `paper.review.md`。

**写作语言规则**：正文用英文撰写（模拟真实审稿场景），每条英文内容后紧跟 `> **中文**：` 块提供完整中文翻译（逐句对应，非摘要）。

**格式与风格参照**：输出严格遵循以下格式标准：

| 要素                        | 格式要求                                                                                                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Section 标题                | `Summary of the paper:` / `Strong points of the paper:` / `Weak points of the paper:` / `Detailed comments:` / `Suggestions for Improvement:` / `Confidential Comments to Editor:` / `Overall Rating:` |
| Summary                     | 一段话，事实性中立语气，不含个人判断。说清即止                                                                                                                                                         |
| Strong points (S1,S2..)     | 独立段落，聚焦一个具体贡献，附锚点。一句讲得清就一句，需要展开就展开                                                                                                                                   |
| Weak points (W1,W2..)       | 独立段落，区分根本性缺陷与可修复问题，附锚点。直接说问题，不绕弯                                                                                                                                       |
| Detailed comments (D1,D2..) | 深入讨论具体技术问题，引用 Section/Figure，使用学术 hedge 语。有些问题三两句话就够，有些需要充分展开——以讲清楚为准，不凑篇幅                                                                           |
| Suggestions for Improvement | 具体可操作的修改建议，每条对应上方 W 或 D 编号                                                                                                                                                         |
| Confidential Comments       | 简短总结论文与 venue 标准的契合度，给出明确录用建议                                                                                                                                                    |
| Overall Rating              | 单一小写词：`accept` / `weak accept` / `weak reject` / `reject`                                                                                                                                        |

**篇幅原则**：每一句都必须有实质信息。能三句话说清的问题不要写五句。需要展开的技术细节不要三句带过。真实审稿人的意见长短不一，关键是句句有用。

审稿输出必须包含（按真实审稿报告的标准结构）：

- **Summary of the paper**：1 段概括论文内容，保持中立、客观、事实性语气。用自己的话复述，证明你充分理解了论文。
- **Strong points of the paper**：S1, S2, S3...，每段 2-4 句，聚焦一个独立优点，附锚点。客观具体，如"该工作提出的 XX 算法在 XX 数据集上取得了 SOTA 结果"。
- **Weak points of the paper**：W1, W2, W3...，每段 2-4 句，区分根本性方法论缺陷与可修复问题，附锚点。切忌空泛——不要只说"创新性不足"，而应指出与哪篇已有工作的关系未澄清。
- **Detailed comments**：D1, D2, D3...，每段 5-8 句，深入讨论具体技术问题。引用 Section/Chapter/Figure。使用学术 hedge 语。可覆盖：技术细节缺失、实验设计缺陷、表述问题、与既有工作的关系未澄清等。
- **Suggestions for Improvement**：针对 Weak points 和 Detailed comments，提出具体、可操作的修改建议。如"建议补充在 XX 数据集上的实验，以验证方法的泛化性"。
- **Confidential Comments to Editor**：简要总结论文与 venue 标准的契合度，给出明确的录用建议。这部分模拟真实审稿中只有编辑看到的内容。
- **Overall Rating**：单一小写词（accept / weak accept / weak reject / reject）。

### Venue Awareness

审稿时以目标会议/期刊的官方录用标准为参照：

- 若用户指定 venue（如"按 ICML 标准审稿"），先搜索该 venue 的官方 reviewer guide、author guide 和录用标准，据此调整评分 bar。
- 若用户未指定 venue，默认以 TMLR/NeurIPS 类顶会标准为参照，并在报告中标注"未指定 venue，以通用顶会标准审稿"。
- 不同 venue 的 Rating 含义不同——例如 TMLR 的 Accept 与 NeurIPS 的 Accept 门槛不同，需在 Rating justification 中体现 venue context。

## 示例

用户说 `审稿这篇论文：@paper.md` → 执行 full 档位审稿：阶段 0 准备（未指定 venue 则以通用顶会标准）→ 阶段 1 扫描通读 → 阶段 2 按五维逐节精读 → 阶段 3 参考模板撰写英文审稿意见（每条后跟中文翻译块），写入 `.paper-review/paper.review.md` → 阶段 4 质量自检后交付。

用户说 `按 ICML 标准做 full review：@paper.md` → 先搜索 ICML 官方 reviewer guide 与录用标准，调整评分 bar，其余流程同上，并在 Rating justification 中体现 venue context。

用户说 `快速审稿这篇论文，按 NeurIPS 标准：@paper.md` → 执行 quick 档位：聚焦 Major Concerns + Rating，输出从简。

## 注意事项

- **不凭空编造**：所有判断必须基于论文原文内容。
- **建设性语气**：Concerns 应保持建设性，避免攻击性措辞。
- **锚点强制**：每个判断必须附精确锚点。
- **区分事实与判断**：对论文内容的陈述与审稿人的评价要明确区分。
- **Rating 一致性**：若 Weak points 数量多且严重，Rating 不应为 accept。
