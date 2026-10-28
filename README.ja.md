<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="skill-shrinker by UniqAI" src="assets/banner.svg" width="1280" height="320">
</picture>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ja&utm_campaign=skill-shrinker)

# skill-shrinker: SKILL.md・AGENTS.md・Cursor ルールを圧縮する

**SKILL.md やエージェント指示ファイルをスリム化します。サイズを計測し、長い部分を references に移し、トリガーはそのまま残します。**

[クイックスタート](#クイックスタート) · [仕組み](#仕組み) · [例](#例) · [インストール](#インストール) · [FAQ](#faq)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · 日本語 · [한국어](README.ko.md)

skill-shrinker は `CLAUDE.md`、`AGENTS.md`、`SKILL.md`、`.cursor/rules` のファイルを圧縮し、Claude Code・Cursor・Codex が 1 ターンごとに読み込むトークンを減らします。中身は、書き換え手順をまとめたスキルと、依存パッケージなしの Python スクリプト 1 本です。スクリプトは重複ルール、矛盾、説明口調の文、長すぎる例、使われていないセクションを見つけ、書き換え前後のトークン数を報告し、MUST / NEVER / ALWAYS / DO NOT を含む文がすべて書き換え後も残っているかを確認します。指示は 1 つも消えず、余計な部分だけがなくなります。

| **行番号つきの監査** | **好みではなくルールで書き換える** | **何も失われていないことを証明する** |
|:---|:---|:---|
| 重複、ほぼ重複、矛盾、埋め草フレーズ、15 行を超えるコードブロック、40 行を超えるセクション、空のセクション。 | 順序の決まった 11 のルール: 制約文は一字一句そのまま、重なりは統合、説明口調の文は削除、概念ごとに例は 1 つ、めったに使わない詳細は `references/` へ。 | `compare` が書き換え前後の表を出力し、各制約文を「維持」「references に移動」「消失」のいずれかとして一覧にします。`--strict` を付けると消失があった時点で CI が失敗します。 |

## クイックスタート

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
python3 ~/.claude/skills/skill-shrinker/scripts/shrink.py audit CLAUDE.md
```

行番号つきの指摘一覧とサイズの行が表示されます。続いて Claude Code で `/skill-shrinker CLAUDE.md`（または単に「この CLAUDE.md は長すぎる」）と伝えると、スキルが元ファイルの隣に書き換え版を作成し、`compare` を実行して、何を移動し、何を削除し、何と何が矛盾していたかを報告します。

## デモ

<img alt="skill-shrinker demo: audit of a 188-line CLAUDE.md, then compare before and after" src="assets/demo.svg" width="820">

この出力は、[`examples/README.md`](examples/README.md) にあるコマンドを `examples/claude-md/` に対して実行した結果を短くまとめたものです。

## 仕組み

1. **計測する。** `shrink.py report FILE` が行数、語数、文字数、トークン数を出力します。`ANTHROPIC_API_KEY` が設定されていれば Anthropic の `count_tokens` による正確な値（ヘッダーにモデル名を表示）、未設定ならローカルの概算値で、その旨が明記されます。キーを設定しない限りデータはマシンの外に出ません。`--tokens estimate` で常にオフライン動作にできます。
2. **監査する。** `shrink.py audit FILE` は行と文の単位で処理します。正規化後の完全一致の重複、語の重なりによるほぼ重複、矛盾（同じ語に対する「always X」と「never X」）、説明口調のフレーズの一覧、長いコードブロック、長いセクション、長い表、空のセクション、繰り返される見出し、そして残さなければならない制約文を検出します。
3. **書き換える。** エージェント（または自分自身）が [`SKILL.md`](SKILL.md) のルールを適用します。制約文はバイト単位で同一のまま、重複は削除、重なりは統合、矛盾は黙って解決せずに報告、説明口調の文は削除、説明文は命令形に、概念ごとに例は 1 つ、セットアップやトラブルシューティングは 1 行のポインタを残して `references/` へ移動、フロントマターとトリガーフレーズには手を付けません。
4. **検証する。** `shrink.py compare BEFORE AFTER` が表を出力し、参照先ファイルの分も合算して、削減したバイトがどこへ行ったかを正直に示し、すべての制約文を確認します。失われた制約文は `LOST:` 付きで表示され、`--strict` なら終了コード 2 で終了します。

同梱のサンプル（`examples/claude-md`、推定トークン数、コマンドは [`examples/README.md`](examples/README.md)）での結果です。

|  | before/CLAUDE.md | after/CLAUDE.md | 変化 |
|:--|--:|--:|--:|
| 行数 | 188 | 54 | -71% |
| 語数 | 1,345 | 486 | -64% |
| 文字数 | 8,413 | 3,169 | -62% |
| トークン数（推定） | 2,468 | 979 | -60% |

セットアップスクリプトとハンドラーの例を受け取った 2 つの参照ファイルは合計 998 推定トークンなので、ファイル一式としては元より 20% 小さく、毎ターン読み込まれる部分は 60% 小さくなっています。制約文は 23 件のうち 21 件が一字一句そのまま維持、1 件は references のみに存在、1 件は意図的に削除（タブ vs スペースという矛盾の負けた側）です。これらの数値は `examples/` 内のファイルに対して `scripts/shrink.py` が出力したものそのままで、ずれるとテストが失敗します。

```
scripts/shrink.py   report | audit | compare      Python 3.9+, stdlib only
SKILL.md            the procedure and the eleven rewrite rules
references/         playbook with before/after snippets, token estimate notes
examples/           two before/after pairs with committed outputs
```

## 例

<details>
<summary><b>説明口調の文に埋もれたルール: 書き換え前 → 後</b></summary>

**書き換え前**

```text
Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert
failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either
rethrow, or log it with `logger.error` and return a typed failure.
```

**書き換え後**

```text
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError`
  (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with
  `logger.error` and return a typed failure.
```

制約文はバイト単位で同一なので、`compare` が検出します。説明口調の文（「Obviously ... should be handled」）はなくなりました。

</details>

<details>
<summary><b>矛盾は推測せずに報告する</b></summary>

```text
CONTRADICTIONS               1
  L39 vs L185
      - Always use tabs for indentation.
      - Never use tabs for indentation.
```

スキルはどちらかの側を選びません。該当するペアを列挙して確認を求めます。無人実行の場合は周囲の記述が裏付ける側を残し、`compare` がもう一方を `LOST:` として表示するので、判断の記録が残ります。

</details>

<details>
<summary><b>SKILL.md 内で重なり合うトリガー</b></summary>

**書き換え前**

```text
- The user asks what changed between two tags.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.
```

**書き換え後**

```text
- What changed between two tags or commits, or since the last release.
```

トリガー語の和集合を保ったまま、2 行減りました。ペア全体は [`examples/skill-md/`](examples/skill-md/) にあります。

</details>

## インストール

指示ファイルを読むエージェントならどれでも使えます。お使いのものを選んでください。要件: Python 3.9+。インストールするパッケージはありません。

<details open>
<summary><b>Claude Code</b>（スキルとして）</summary>

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
```
その後 Claude Code で `/skill-shrinker` と入力するか、やりたいことをそのまま伝えてください。スキルは description に基づいて起動します。
グローバルではなくプロジェクト単位で使う場合は、プロジェクト内の `.claude/skills/skill-shrinker` に clone してください。

Agent Skills ディレクトリから: `npx skills add uniqaiapp/skill-shrinker`。

</details>

<details>
<summary><b>Claude Code</b>（プラグインとして。uniqaiapp マーケットプレイス公開後）</summary>

```
/plugin marketplace add uniqaiapp/skills
/plugin install skill-shrinker@uniqaiapp
```

</details>

<details>
<summary><b>Cursor</b></summary>

[`SKILL.md`](SKILL.md)、`scripts/`、[`.cursor/rules/skill-shrinker.mdc`](.cursor/rules/skill-shrinker.mdc) をプロジェクトにコピーしてください。ルールファイルにスキルが埋め込まれています。

</details>

<details>
<summary><b>Codex / AGENTS.md を読むエージェント全般</b></summary>

`SKILL.md` と `scripts/` を `.agents/skills/skill-shrinker/` にコピーし、[`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) のスニペットを `AGENTS.md` に追加してください。

</details>

<details>
<summary><b>エージェントなしで使う</b></summary>

すべてのコマンドは単体で動きます: `python3 scripts/shrink.py --help`。`SKILL.md` のルールは、人間が編集するときのチェックリストとしてもそのまま読めます。

</details>

## FAQ

<details>
<summary><b>ファイルは自動で書き換えられますか？</b></summary>

スクリプトがファイルに書き込むことはなく、出力するだけです。スキルは、上書きを指定しない限り元ファイルの隣に新しいファイル（たとえば `CLAUDE.shrunk.md`）として書き換え版を保存するので、常に diff を確認できます。

</details>

<details>
<summary><b>トークン数はどのくらい正確ですか？</b></summary>

`ANTHROPIC_API_KEY` が設定されていれば、出力に表示されるモデル（デフォルトは `claude-opus-5-5`、`SHRINK_MODEL` で変更可）に対する Anthropic の `count_tokens` による正確な値です。キーがない場合は文書化されたヒューリスティック（[`references/token-estimate.md`](references/token-estimate.md)）で、どのトークナイザーに対しても校正されていません。絶対値は目安と考え、同じ方法で算出した数値同士だけを比較し、コードや非ラテン文字のテキストでは誤差が大きくなると見込んでください。推定値の場合、すべての表に `estimate` と表示されます。

</details>

<details>
<summary><b>指示の意味が変わってしまうことはありませんか？</b></summary>

そのための制約チェックです。MUST、NEVER、ALWAYS、DO NOT などの語を含むすべての文は、埋め草を取り除いたうえで元ファイルと書き換え版の間で照合され、短縮されただけでも「消失」として扱われます。これらの語を含まない緩いルールはスクリプトでは保護されないので、diff を読んでください。スキルはエージェントに対し、完全な重複でなかった削除行をすべて列挙するよう指示します。

</details>

<details>
<summary><b>ファイルを捨てて書き直したほうが早いのでは？</b></summary>

それが正解のこともあり、その場合も監査は役に立ちます。制約文の一覧が、必ず引き継ぐべき部分だからです。ただ、ほとんどのファイルはそこまでひどくありません。本当のルールという核があり、その周りをかつては役に立った説明や例が取り囲んでいるだけです。説明を `references/` に移しておけば、再び必要になる日のために残しつつ、それ以外のターンではコストがゼロになります。

</details>

<details>
<summary><b>英語以外のファイルでも動きますか？</b></summary>

サイズ計測と重複検出はどの言語でも動きます。説明口調のフレーズの一覧と制約キーワードは英語なので、ロシア語やドイツ語のルールは検出も保護もされません。フレーズ一覧を追加するプルリクエストを歓迎します。[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

</details>

## 関連プロジェクト

- [token-diet](https://github.com/uniqaiapp/token-diet): 意味を失わずにプロンプトとコンテキストのトークンを削減します。計測可能なルール、標準ライブラリのみの推定ツール、書き換え前後の例つき。skill-shrinker は同じ考え方を指示ファイルそのものに適用したものです。
- [model-router](https://github.com/uniqaiapp/model-router): タスクをこなせる中で最も安いモデルを選びます。ルール表と、種類・長さ・リスクでタスクを振り分ける標準ライブラリのみのスクリプト。
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): ロシア語テキストから AI 臭い埋め草を取り除きます。典型的な癖を検出して書き換えるスキルと標準ライブラリのみのスクリプト。

## コントリビュート

Issue とプルリクエストを歓迎します。変更は小さくまとめ、PR の説明に書き換え前後の例を添えてください。
ローカルでのチェック（`python3 tests/run.py`、依存なし）は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>開発: <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ja&utm_campaign=skill-shrinker">UniqAI</a> — Kling 3.0、Veo 3、Flux、Nano Banana と GPT-5/Claude/Gemini/Grok をひとつのアプリで。自分たちのスキルを短く保つために作りました。</sub>

</div>
