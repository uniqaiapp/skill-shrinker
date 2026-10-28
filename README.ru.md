<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="skill-shrinker by UniqAI" src="assets/banner.svg" width="1280" height="320">
</picture>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#установка)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#установка)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#установка)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ru&utm_campaign=skill-shrinker)

# skill-shrinker: сжатие SKILL.md, AGENTS.md и правил Cursor

**Сокращает любой SKILL.md или файл инструкций для агента: измеряет размер, выносит длинные куски в references, не трогает триггеры.**

[Быстрый старт](#быстрый-старт) · [Как это работает](#как-это-работает) · [Примеры](#примеры) · [Установка](#установка) · [FAQ](#faq)

</div>

[English](README.md) · Русский · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

skill-shrinker сжимает файлы `CLAUDE.md`, `AGENTS.md`, `SKILL.md` и `.cursor/rules`, чтобы Claude Code, Cursor и Codex загружали меньше токенов на каждом ходу. Это скилл (процедура переписывания) плюс один Python-скрипт без зависимостей, который находит дублирующиеся правила, противоречия, «воду», длинные примеры и мёртвые разделы, считает токены до и после и проверяет, что каждое предложение с MUST / NEVER / ALWAYS / DO NOT пережило переписывание. Все инструкции остаются, уходит только лишнее.

| **Аудит с номерами строк** | **Переписывание по правилам, а не на вкус** | **Доказательство, что ничего не потеряно** |
|:---|:---|:---|
| Дубликаты, почти-дубликаты, противоречия, слова-паразиты, блоки кода длиннее 15 строк, разделы длиннее 40 строк, пустые разделы. | Одиннадцать правил по порядку: ограничения дословно, пересечения объединить, повествование убрать, один пример на понятие, редкие детали в `references/`. | `compare` печатает таблицу «до/после» и помечает каждое предложение-ограничение как сохранённое, вынесенное в references или потерянное. `--strict` валит CI при потере. |

## Быстрый старт

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
python3 ~/.claude/skills/skill-shrinker/scripts/shrink.py audit CLAUDE.md
```

Вы получаете список находок с номерами строк и строку с размером. Дальше в Claude Code: `/skill-shrinker CLAUDE.md` (или просто «этот CLAUDE.md слишком длинный»), и скилл перепишет файл рядом с оригиналом, запустит `compare` и расскажет, что вынесено, что удалено и что чему противоречит.

## Демо

<img alt="skill-shrinker demo: audit of a 188-line CLAUDE.md, then compare before and after" src="assets/demo.svg" width="820">

Это сокращённая запись команд из [`examples/README.md`](examples/README.md), выполненных на `examples/claude-md/`.

## Как это работает

1. **Измерить.** `shrink.py report FILE` печатает строки, слова, символы и токены. Токены точные (Anthropic `count_tokens`, модель указана в заголовке), если задан `ANTHROPIC_API_KEY`; иначе локальная оценка, которая так и подписана. Без ключа ничего не уходит с машины; `--tokens estimate` принудительно включает офлайн-режим.
2. **Проверить.** `shrink.py audit FILE` работает на уровне строк и предложений: точные дубликаты после нормализации, почти-дубликаты по пересечению слов, противоречия («always X» против «never X» на одних и тех же словах), список повествовательных оборотов, длинные блоки кода, длинные разделы, длинные таблицы, пустые разделы, повторяющиеся заголовки и предложения-ограничения, которые обязаны уцелеть.
3. **Переписать.** Агент (или вы) применяет правила из [`SKILL.md`](SKILL.md): ограничения байт в байт, дубликаты долой, пересечения объединены, противоречия показаны, а не разрешены молча, повествование удалено, проза превращена в императивы, один пример на понятие, установка и устранение неполадок вынесены в `references/` с однострочной ссылкой, фронтматтер и триггерные фразы не тронуты.
4. **Проверить результат.** `shrink.py compare BEFORE AFTER` печатает таблицу, прибавляет размер вынесенных файлов, чтобы экономия честно показывала, куда ушли байты, и сверяет каждое ограничение. Потерянные печатаются с пометкой `LOST:`; `--strict` завершается с кодом 2.

На встроенном примере (`examples/claude-md`, оценка токенов, команда в [`examples/README.md`](examples/README.md)):

|  | before/CLAUDE.md | after/CLAUDE.md | изменение |
|:--|--:|--:|--:|
| строки | 188 | 54 | -71% |
| слова | 1,345 | 486 | -64% |
| символы | 8,413 | 3,169 | -62% |
| токены (оценка) | 2,468 | 979 | -60% |

Два файла в references, куда ушли скрипт установки и пример обработчика, вместе дают 998 оценочных токенов, так что весь набор стал на 20% меньше оригинала, а часть, которая загружается на каждом ходу, — на 60%. На входе 23 предложения-ограничения, 21 сохранено дословно, 1 осталось только в references, 1 потеряно намеренно (проигравшая сторона противоречия «табы или пробелы»). Эти числа — ровно то, что `scripts/shrink.py` печатает на файлах из `examples/`; если они разойдутся, тесты упадут.

```
scripts/shrink.py   report | audit | compare      Python 3.9+, stdlib only
SKILL.md            the procedure and the eleven rewrite rules
references/         playbook with before/after snippets, token estimate notes
examples/           two before/after pairs with committed outputs
```

## Примеры

<details>
<summary><b>Правило, утопленное в повествовании: до → после</b></summary>

**До**

```text
Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert
failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either
rethrow, or log it with `logger.error` and return a typed failure.
```

**После**

```text
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError`
  (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with
  `logger.error` and return a typed failure.
```

Предложение-ограничение совпадает байт в байт, `compare` его находит. Повествование («Obviously ... should be handled») исчезло.

</details>

<details>
<summary><b>Противоречие: показано, а не угадано</b></summary>

```text
CONTRADICTIONS               1
  L39 vs L185
      - Always use tabs for indentation.
      - Never use tabs for indentation.
```

Скилл не выбирает сторону. Он показывает пару и спрашивает; в автономном запуске оставляет вариант, который подтверждается контекстом вокруг, а `compare` показывает второй как `LOST:`, чтобы решение было зафиксировано.

</details>

<details>
<summary><b>Пересекающиеся триггеры в SKILL.md</b></summary>

**До**

```text
- The user asks what changed between two tags.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.
```

**После**

```text
- What changed between two tags or commits, or since the last release.
```

Объединение триггерных слов сохранено, на две строки меньше. Полная пара: [`examples/skill-md/`](examples/skill-md/).

</details>

## Установка

Работает с любым агентом, который читает файлы инструкций. Выберите свой. Требования: Python 3.9+. Пакеты ставить не нужно.

<details open>
<summary><b>Claude Code</b> (как скилл)</summary>

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
```
Затем в Claude Code наберите `/skill-shrinker` или просто опишите задачу: скилл срабатывает по своему описанию.
Локально для проекта вместо глобальной установки: клонируйте в `.claude/skills/skill-shrinker` внутри проекта.

Каталог Agent Skills: `npx skills add uniqaiapp/skill-shrinker`.

</details>

<details>
<summary><b>Claude Code</b> (как плагин, когда будет опубликован маркетплейс uniqaiapp)</summary>

```
/plugin marketplace add uniqaiapp/skills
/plugin install skill-shrinker@uniqaiapp
```

</details>

<details>
<summary><b>Cursor</b></summary>

Скопируйте [`SKILL.md`](SKILL.md), `scripts/` и [`.cursor/rules/skill-shrinker.mdc`](.cursor/rules/skill-shrinker.mdc) в свой проект. Файл правила встраивает скилл.

</details>

<details>
<summary><b>Codex / любой агент, который читает AGENTS.md</b></summary>

Скопируйте `SKILL.md` и `scripts/` в `.agents/skills/skill-shrinker/` и добавьте сниппет из [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) в свой `AGENTS.md`.

</details>

<details>
<summary><b>Без агента</b></summary>

Каждая команда работает сама по себе: `python3 scripts/shrink.py --help`. Правила из `SKILL.md` читаются и как чек-лист для редактора-человека.

</details>

## FAQ

<details>
<summary><b>Он правит мой файл сам?</b></summary>

Скрипт никогда не пишет в ваши файлы, он только печатает. Скилл записывает переписанную версию в новый файл рядом с оригиналом (например, `CLAUDE.shrunk.md`), если вы не попросили править на месте, так что диф у вас есть всегда.

</details>

<details>
<summary><b>Насколько точен подсчёт токенов?</b></summary>

С заданным `ANTHROPIC_API_KEY` это точное число из `count_tokens` Anthropic для модели, указанной в выводе (по умолчанию `claude-opus-5-5`, переопределяется через `SHRINK_MODEL`). Без ключа это задокументированная эвристика ([`references/token-estimate.md`](references/token-estimate.md)), не откалиброванная ни под один токенизатор: абсолютные значения считайте приблизительными, сравнивайте только числа, полученные одним и тем же способом, и ждите большей погрешности на коде и нелатинском тексте. В каждой таблице стоит `estimate`, если это оценка.

</details>

<details>
<summary><b>Изменится ли смысл моих инструкций?</b></summary>

Для этого и есть проверка ограничений. Каждое предложение со словами MUST, NEVER, ALWAYS, DO NOT и похожими сверяется между оригиналом и переписанной версией после удаления «воды»; сокращение такого предложения считается потерей. Мягкие правила без этих слов скрипт не защищает, поэтому читайте диф. Скилл требует от агента перечислить каждую удалённую строку, которая не была точным дубликатом.

</details>

<details>
<summary><b>Почему бы просто не удалить файл и не начать заново?</b></summary>

Иногда это правильный ход, и аудит помогает и здесь: список ограничений — это то, что обязательно нужно перенести. Но большинство файлов не настолько плохи: у них есть ядро из настоящих правил, обёрнутое в объяснения и примеры, которые когда-то были полезны. Перенос объяснений в `references/` сохраняет их на тот день, когда они снова понадобятся, и ничего не стоит на всех остальных ходах.

</details>

<details>
<summary><b>Работает ли он с файлами не на английском?</b></summary>

Подсчёт размера и поиск дубликатов работают на любом языке. Список повествовательных оборотов и ключевые слова ограничений английские, поэтому правила на русском или немецком не помечаются и не защищаются. Пул-реквесты со списками фраз приветствуются; см. [CONTRIBUTING.md](CONTRIBUTING.md).

</details>

## Похожие проекты

- [token-diet](https://github.com/uniqaiapp/token-diet): сокращение токенов в промптах и контексте без потери смысла, измеримые правила, оценщик на stdlib и примеры «до/после». skill-shrinker — та же идея, применённая к самим файлам инструкций.
- [model-router](https://github.com/uniqaiapp/model-router): выбор самой дешёвой модели, которая справится с задачей, таблица правил и скрипт на stdlib, который маршрутизирует задачи по типу, длине и риску.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): удаление ИИ-штампов из русского текста, скилл плюс скрипт на stdlib, который находит и переписывает типичные признаки.

## Как помочь проекту

Issues и пул-реквесты приветствуются. Делайте изменения небольшими и прикладывайте пример «до/после» в описании PR.
Локальные проверки описаны в [CONTRIBUTING.md](CONTRIBUTING.md) (`python3 tests/run.py`, без зависимостей).

## Лицензия

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Сделано в <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ru&utm_campaign=skill-shrinker">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana и GPT-5/Claude/Gemini/Grok в одном приложении. Мы написали этот инструмент, чтобы держать короткими собственные скиллы.</sub>

</div>
