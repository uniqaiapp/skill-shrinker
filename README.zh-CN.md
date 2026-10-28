<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="skill-shrinker by UniqAI" src="assets/banner.svg" width="1280" height="320">
</picture>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#安装)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#安装)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#安装)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-zh-cn&utm_campaign=skill-shrinker)

# skill-shrinker：压缩 SKILL.md、AGENTS.md 和 Cursor 规则

**给任何 SKILL.md 或 agent 指令文件瘦身：测量体积，把长内容移到 references，触发条件原样保留。**

[快速开始](#快速开始) · [工作原理](#工作原理) · [示例](#示例) · [安装](#安装) · [常见问题](#常见问题)

</div>

[English](README.md) · [Русский](README.ru.md) · 简体中文 · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

skill-shrinker 用来压缩 `CLAUDE.md`、`AGENTS.md`、`SKILL.md` 和 `.cursor/rules` 文件，让 Claude Code、Cursor 和 Codex 每轮对话加载更少的 token。它由一个技能（改写流程）和一个零依赖的 Python 脚本组成：脚本负责找出重复规则、互相矛盾的规则、叙述性废话、过长的示例和失效的章节，报告改写前后的 token 数，并检查每一句 MUST / NEVER / ALWAYS / DO NOT 是否在改写后幸存。所有指令一条不少，只去掉填充内容。

| **带行号的审计** | **按规则改写，而不是凭感觉** | **证明没有丢失任何内容** |
|:---|:---|:---|
| 重复、近似重复、矛盾、填充短语、超过 15 行的代码块、超过 40 行的章节、空章节。 | 十一条有序规则：约束原文保留，重叠内容合并，叙述删掉，每个概念只留一个示例，少用的细节移入 `references/`。 | `compare` 打印改写前后的对比表，并逐句列出每条约束是保留、移入 references 还是丢失。`--strict` 在有丢失时让 CI 失败。 |

## 快速开始

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
python3 ~/.claude/skills/skill-shrinker/scripts/shrink.py audit CLAUDE.md
```

你会得到一份带行号的问题清单和一行体积统计。然后在 Claude Code 里输入 `/skill-shrinker CLAUDE.md`（或者直接说“这个 CLAUDE.md 太长了”），技能会在原文件旁边写出改写版本，运行 `compare`，并汇报哪些内容被移走、哪些被删除、哪些互相矛盾。

## 演示

<img alt="skill-shrinker demo: audit of a 188-line CLAUDE.md, then compare before and after" src="assets/demo.svg" width="820">

这段记录是在 `examples/claude-md/` 上执行 [`examples/README.md`](examples/README.md) 中命令的精简版。

## 工作原理

1. **测量。** `shrink.py report FILE` 打印行数、词数、字符数和 token 数。设置了 `ANTHROPIC_API_KEY` 时，token 数是精确值（Anthropic `count_tokens`，所用模型在表头注明）；否则是本地估算值，并会明确标注为估算。不设置 key 就不会有任何数据离开本机；`--tokens estimate` 强制离线。
2. **审计。** `shrink.py audit FILE` 按行和按句工作：归一化后的完全重复、按词重叠度判断的近似重复、矛盾（同一组词上“always X”对“never X”）、一份叙述性短语清单、过长的代码块、过长的章节、过长的表格、空章节、重复的标题，以及必须保留下来的约束句。
3. **改写。** 由 agent（或你自己）按 [`SKILL.md`](SKILL.md) 中的规则执行：约束逐字节保持一致，重复删除，重叠合并，矛盾只报告、不私自裁决，叙述删掉，散文改成祈使句，每个概念只留一个示例，安装和排错内容移入 `references/` 并留一行指引，frontmatter 和触发短语一律不动。
4. **验证。** `shrink.py compare BEFORE AFTER` 打印对比表，把被引用的文件也一并计入，这样节省的数字才诚实地反映字节去了哪里，并逐条检查约束。丢失的约束以 `LOST:` 打印；`--strict` 时退出码为 2。

在自带的样例上（`examples/claude-md`，估算 token，命令见 [`examples/README.md`](examples/README.md)）：

|  | before/CLAUDE.md | after/CLAUDE.md | 变化 |
|:--|--:|--:|--:|
| 行数 | 188 | 54 | -71% |
| 词数 | 1,345 | 486 | -64% |
| 字符数 | 8,413 | 3,169 | -62% |
| token（估算） | 2,468 | 979 | -60% |

承接安装脚本和 handler 示例的两个 reference 文件合计 998 个估算 token，所以整套文件比原来小 20%，而每轮都会加载的那部分小了 60%。23 条约束句输入，21 条逐字保留，1 条只存在于 references，1 条是有意丢弃的（tabs 与 spaces 矛盾中落败的一方）。这些数字就是 `scripts/shrink.py` 在 `examples/` 下的文件上打印出来的结果；一旦漂移，测试就会失败。

```
scripts/shrink.py   report | audit | compare      Python 3.9+, stdlib only
SKILL.md            the procedure and the eleven rewrite rules
references/         playbook with before/after snippets, token estimate notes
examples/           two before/after pairs with committed outputs
```

## 示例

<details>
<summary><b>埋在叙述里的规则：改写前 → 改写后</b></summary>

**改写前**

```text
Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert
failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either
rethrow, or log it with `logger.error` and return a typed failure.
```

**改写后**

```text
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError`
  (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with
  `logger.error` and return a typed failure.
```

约束句逐字节一致，`compare` 能找到它。叙述部分（“Obviously ... should be handled”）没了。

</details>

<details>
<summary><b>矛盾：只报告，不猜测</b></summary>

```text
CONTRADICTIONS               1
  L39 vs L185
      - Always use tabs for indentation.
      - Never use tabs for indentation.
```

技能不会替你选边。它列出这一对并询问你；在无人值守的运行中，它保留有上下文证据支持的那一条，`compare` 会把另一条显示为 `LOST:`，这样决定有据可查。

</details>

<details>
<summary><b>SKILL.md 里互相重叠的触发条件</b></summary>

**改写前**

```text
- The user asks what changed between two tags.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.
```

**改写后**

```text
- What changed between two tags or commits, or since the last release.
```

触发词的并集完整保留，少了两行。完整的对照见 [`examples/skill-md/`](examples/skill-md/)。

</details>

## 安装

适用于任何会读取指令文件的 agent，按你用的选。要求：Python 3.9+。无需安装任何包。

<details open>
<summary><b>Claude Code</b>（作为技能）</summary>

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
```
然后在 Claude Code 里输入 `/skill-shrinker`，或者直接描述任务；技能会根据自身的 description 触发。
想装成项目级而不是全局：克隆到项目内的 `.claude/skills/skill-shrinker`。

Agent Skills 目录：`npx skills add uniqaiapp/skill-shrinker`。

</details>

<details>
<summary><b>Claude Code</b>（作为插件，待 uniqaiapp marketplace 发布后可用）</summary>

```
/plugin marketplace add uniqaiapp/skills
/plugin install skill-shrinker@uniqaiapp
```

</details>

<details>
<summary><b>Cursor</b></summary>

把 [`SKILL.md`](SKILL.md)、`scripts/` 和 [`.cursor/rules/skill-shrinker.mdc`](.cursor/rules/skill-shrinker.mdc) 复制到你的项目里。规则文件内嵌了这个技能。

</details>

<details>
<summary><b>Codex / 任何读取 AGENTS.md 的 agent</b></summary>

把 `SKILL.md` 和 `scripts/` 复制到 `.agents/skills/skill-shrinker/`，再把 [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) 里的片段加到你的 `AGENTS.md` 中。

</details>

<details>
<summary><b>不用 agent</b></summary>

每条命令都能独立运行：`python3 scripts/shrink.py --help`。`SKILL.md` 里的规则也可以直接当作人工编辑的检查清单来读。

</details>

## 常见问题

<details>
<summary><b>它会自动修改我的文件吗？</b></summary>

脚本从不写入你的文件，只负责打印。技能会把改写结果写到原文件旁边的新文件里（例如 `CLAUDE.shrunk.md`），除非你要求原地修改，所以你随时能看到 diff。

</details>

<details>
<summary><b>token 数有多准？</b></summary>

设置了 `ANTHROPIC_API_KEY` 时，它是 Anthropic `count_tokens` 对输出中注明的模型给出的精确计数（默认 `claude-opus-5-5`，可用 `SHRINK_MODEL` 覆盖）。没有 key 时，它是一个有文档说明的启发式估算（[`references/token-estimate.md`](references/token-estimate.md)），没有针对任何 tokenizer 校准过，所以绝对值只能当作粗略参考，只比较用同一方式得出的数字，并且在代码和非拉丁文字上误差会更大。只要是估算值，表格里一律写明 `estimate`。

</details>

<details>
<summary><b>它会改变我指令的含义吗？</b></summary>

约束检查就是为此而设。每一句含有 MUST、NEVER、ALWAYS、DO NOT 及类似词的句子，都会在去掉填充词之后在原文和改写版之间做匹配；缩写了一句也算丢失。不含这些词的软规则不受脚本保护，所以请看 diff。技能会要求 agent 列出每一行被删除且不是完全重复的内容。

</details>

<details>
<summary><b>为什么不直接删掉文件重写？</b></summary>

有时这确实是对的，审计在这种情况下同样有用：约束清单就是你必须带过去的那部分。但大多数文件没那么糟；它们有一个真正的规则内核，外面裹着曾经有用的解释和示例。把解释移到 `references/`，既为日后需要时保留了它们，又不在其他任何一轮对话中付出代价。

</details>

<details>
<summary><b>非英文文件能用吗？</b></summary>

体积统计和重复检测对任何语言都有效。叙述短语清单和约束关键词是英文的，所以俄语或德语规则既不会被标记，也不受保护。欢迎提交 pull request 补充短语清单；见 [CONTRIBUTING.md](CONTRIBUTING.md)。

</details>

## 相关项目

- [token-diet](https://github.com/uniqaiapp/token-diet)：在不丢失语义的前提下削减 prompt 和上下文 token，可度量的规则、stdlib 估算器，以及前后对照示例。skill-shrinker 是把同一思路用在指令文件本身上。
- [model-router](https://github.com/uniqaiapp/model-router)：按任务选出能胜任的最便宜模型，一张规则表加一个 stdlib 脚本，按类型、长度和风险路由任务。
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru)：去掉俄语文本里的 AI 味填充，一个技能加一个 stdlib 脚本，标记并改写常见的 AI 痕迹。

## 参与贡献

欢迎提 issue 和 pull request。改动尽量小，并在 PR 描述里附上前后对照示例。
本地检查见 [CONTRIBUTING.md](CONTRIBUTING.md)（`python3 tests/run.py`，无依赖）。

## 许可证

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>由 <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-zh-cn&utm_campaign=skill-shrinker">UniqAI</a> 开发 — Kling 3.0、Veo 3、Flux、Nano Banana 和 GPT-5/Claude/Gemini/Grok 集于一个应用。我们写这个工具是为了让自家的技能保持精简。</sub>

</div>
