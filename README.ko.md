<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="skill-shrinker by UniqAI" src="assets/banner.svg" width="1280" height="320">
</picture>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ko&utm_campaign=skill-shrinker)

# skill-shrinker: SKILL.md, AGENTS.md, Cursor 규칙 압축 도구

**SKILL.md나 에이전트 지시 파일을 줄입니다. 크기를 측정하고, 긴 내용은 references로 옮기고, 트리거는 그대로 유지합니다.**

[빠른 시작](#빠른-시작) · [작동 방식](#작동-방식) · [예시](#예시) · [설치](#설치) · [FAQ](#faq)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · 한국어

skill-shrinker는 `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `.cursor/rules` 파일을 압축해서 Claude Code, Cursor, Codex가 매 턴마다 읽어 들이는 토큰을 줄입니다. 구성은 스킬(다시 쓰기 절차) 하나와 의존성 없는 Python 스크립트 하나입니다. 스크립트는 중복 규칙, 모순, 서술형 문장, 긴 예시, 죽은 섹션을 찾아내고, 전후 토큰 수를 보고하며, MUST / NEVER / ALWAYS / DO NOT 문장이 다시 쓴 뒤에도 전부 남아 있는지 확인합니다. 지시는 모두 남고, 군더더기만 빠집니다.

| **줄 번호가 붙은 감사** | **취향이 아니라 규칙대로 다시 쓰기** | **아무것도 잃지 않았다는 증명** |
|:---|:---|:---|
| 중복, 유사 중복, 모순, 군더더기 표현, 15줄이 넘는 코드 블록, 40줄이 넘는 섹션, 빈 섹션. | 순서가 정해진 규칙 열한 개: 제약은 원문 그대로, 겹치는 내용은 병합, 서술은 제거, 개념당 예시 하나, 드문 세부 사항은 `references/`로. | `compare`가 전후 비교표를 출력하고 제약 문장마다 유지, references로 이동, 손실 중 하나로 표시합니다. `--strict`를 주면 손실이 있을 때 CI가 실패합니다. |

## 빠른 시작

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
python3 ~/.claude/skills/skill-shrinker/scripts/shrink.py audit CLAUDE.md
```

줄 번호가 붙은 발견 사항 목록과 크기 한 줄이 출력됩니다. 그다음 Claude Code에서 `/skill-shrinker CLAUDE.md`를 입력하거나 그냥 "이 CLAUDE.md가 너무 길다"고 말하면, 스킬이 원본 옆에 다시 쓴 파일을 만들고 `compare`를 실행한 뒤 무엇이 옮겨졌고, 무엇이 제거됐고, 무엇이 무엇과 모순되는지 보고합니다.

## 데모

<img alt="skill-shrinker demo: audit of a 188-line CLAUDE.md, then compare before and after" src="assets/demo.svg" width="820">

위 기록은 [`examples/README.md`](examples/README.md)의 명령을 `examples/claude-md/`에 실행한 결과를 줄인 것입니다.

## 작동 방식

1. **측정.** `shrink.py report FILE`은 줄, 단어, 문자, 토큰 수를 출력합니다. `ANTHROPIC_API_KEY`가 설정되어 있으면 토큰 수는 정확한 값(Anthropic `count_tokens`, 모델명은 헤더에 표시)이고, 없으면 로컬 추정치이며 추정치라고 표시됩니다. 키를 설정하지 않는 한 어떤 데이터도 기기 밖으로 나가지 않습니다. `--tokens estimate`를 주면 오프라인으로 강제합니다.
2. **감사.** `shrink.py audit FILE`은 줄과 문장 단위로 동작합니다. 정규화 후 완전 중복, 단어 겹침 기준 유사 중복, 모순(같은 단어에 대한 "always X"와 "never X"), 서술형 표현 목록, 긴 코드 블록, 긴 섹션, 긴 표, 빈 섹션, 반복되는 제목, 그리고 반드시 살아남아야 하는 제약 문장을 찾습니다.
3. **다시 쓰기.** 에이전트(또는 사용자)가 [`SKILL.md`](SKILL.md)의 규칙을 적용합니다. 제약은 바이트 단위로 동일하게, 중복은 제거, 겹치는 내용은 병합, 모순은 조용히 해결하지 않고 보고, 서술은 삭제, 산문은 명령문으로, 개념당 예시 하나, 설정과 문제 해결은 한 줄짜리 포인터만 남기고 `references/`로 이동, 프런트매터와 트리거 문구는 손대지 않습니다.
4. **검증.** `shrink.py compare BEFORE AFTER`가 비교표를 출력하고, 참조 파일까지 합산해서 바이트가 어디로 갔는지 정직하게 보여 주며, 제약을 하나씩 확인합니다. 손실된 제약은 `LOST:`로 출력되고, `--strict`를 주면 종료 코드 2로 끝납니다.

포함된 샘플(`examples/claude-md`, 토큰 추정치, 명령은 [`examples/README.md`](examples/README.md) 참고)에 대한 결과입니다.

|  | before/CLAUDE.md | after/CLAUDE.md | 변화 |
|:--|--:|--:|--:|
| 줄 | 188 | 54 | -71% |
| 단어 | 1,345 | 486 | -64% |
| 문자 | 8,413 | 3,169 | -62% |
| 토큰(추정) | 2,468 | 979 | -60% |

설정 스크립트와 핸들러 예시를 받아 간 참조 파일 두 개는 합쳐서 추정 998토큰이므로, 전체 세트는 원본보다 20% 작아지고 매 턴 로드되는 부분은 60% 작아집니다. 제약 문장 23개 중 21개는 원문 그대로 유지, 1개는 references에만 존재, 1개는 의도적으로 손실(탭 대 스페이스 모순에서 진 쪽)입니다. 이 숫자는 `scripts/shrink.py`가 `examples/`의 파일에 대해 출력하는 값 그대로이며, 값이 달라지면 테스트가 실패합니다.

```
scripts/shrink.py   report | audit | compare      Python 3.9+, stdlib only
SKILL.md            the procedure and the eleven rewrite rules
references/         playbook with before/after snippets, token estimate notes
examples/           two before/after pairs with committed outputs
```

## 예시

<details>
<summary><b>서술 속에 묻힌 규칙: 전 → 후</b></summary>

**전**

```text
Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert
failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either
rethrow, or log it with `logger.error` and return a typed failure.
```

**후**

```text
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError`
  (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with
  `logger.error` and return a typed failure.
```

제약 문장은 바이트 단위로 동일하므로 `compare`가 찾아냅니다. 서술("Obviously ... should be handled")은 사라졌습니다.

</details>

<details>
<summary><b>모순은 추측하지 않고 보고합니다</b></summary>

```text
CONTRADICTIONS               1
  L39 vs L185
      - Always use tabs for indentation.
      - Never use tabs for indentation.
```

스킬은 한쪽 편을 들지 않습니다. 쌍을 나열하고 묻습니다. 무인 실행에서는 주변 근거가 뒷받침하는 쪽을 남기고, `compare`가 다른 쪽을 `LOST:`로 표시해서 결정이 기록에 남습니다.

</details>

<details>
<summary><b>SKILL.md에서 겹치는 트리거</b></summary>

**전**

```text
- The user asks what changed between two tags.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.
```

**후**

```text
- What changed between two tags or commits, or since the last release.
```

트리거 단어의 합집합은 유지하면서 두 줄이 줄었습니다. 전체 쌍은 [`examples/skill-md/`](examples/skill-md/)에 있습니다.

</details>

## 설치

지시 파일을 읽는 모든 에이전트에서 동작합니다. 사용하는 것을 고르세요. 요구 사항: Python 3.9+. 설치할 패키지는 없습니다.

<details open>
<summary><b>Claude Code</b>(스킬로 설치)</summary>

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
```
그다음 Claude Code에서 `/skill-shrinker`를 입력하거나 그냥 작업을 설명하면 됩니다. 스킬은 description을 기준으로 트리거됩니다.
전역 대신 프로젝트 로컬로 쓰려면 프로젝트 안의 `.claude/skills/skill-shrinker`에 clone하세요.

Agent Skills 디렉터리: `npx skills add uniqaiapp/skill-shrinker`.

</details>

<details>
<summary><b>Claude Code</b>(플러그인으로 설치, uniqaiapp 마켓플레이스 공개 이후)</summary>

```
/plugin marketplace add uniqaiapp/skills
/plugin install skill-shrinker@uniqaiapp
```

</details>

<details>
<summary><b>Cursor</b></summary>

[`SKILL.md`](SKILL.md), `scripts/`, [`.cursor/rules/skill-shrinker.mdc`](.cursor/rules/skill-shrinker.mdc)를 프로젝트에 복사하세요. 규칙 파일이 스킬을 포함합니다.

</details>

<details>
<summary><b>Codex / AGENTS.md를 읽는 모든 에이전트</b></summary>

`SKILL.md`와 `scripts/`를 `.agents/skills/skill-shrinker/`에 복사하고, [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md)의 스니펫을 `AGENTS.md`에 추가하세요.

</details>

<details>
<summary><b>에이전트 없이</b></summary>

모든 명령은 단독으로 실행됩니다: `python3 scripts/shrink.py --help`. `SKILL.md`의 규칙은 사람이 직접 편집할 때 체크리스트로 써도 잘 읽힙니다.

</details>

## FAQ

<details>
<summary><b>파일을 자동으로 수정하나요?</b></summary>

스크립트는 파일에 쓰지 않고 출력만 합니다. 스킬은 제자리 수정을 요청하지 않는 한 원본 옆에 새 파일(예: `CLAUDE.shrunk.md`)로 결과를 쓰므로, 항상 diff를 볼 수 있습니다.

</details>

<details>
<summary><b>토큰 수는 얼마나 정확한가요?</b></summary>

`ANTHROPIC_API_KEY`가 설정되어 있으면 출력에 표시된 모델(기본값 `claude-opus-5-5`, `SHRINK_MODEL`로 변경 가능)에 대해 Anthropic `count_tokens`가 돌려주는 정확한 값입니다. 키가 없으면 문서화된 휴리스틱([`references/token-estimate.md`](references/token-estimate.md))을 쓰는데, 어떤 토크나이저에도 보정되어 있지 않으므로 절댓값은 대략적인 수치로 보고, 같은 방식으로 산출한 숫자끼리만 비교하고, 코드와 비라틴 문자 텍스트에서는 오차가 더 크다고 생각하세요. 추정치일 때는 모든 표에 `estimate`라고 표시됩니다.

</details>

<details>
<summary><b>지시의 의미가 바뀌지는 않나요?</b></summary>

그래서 제약 검사가 있습니다. MUST, NEVER, ALWAYS, DO NOT 같은 단어가 들어간 모든 문장은 군더더기를 제거한 뒤 원본과 다시 쓴 파일 사이에서 대조되며, 문장을 줄이기만 해도 손실로 셉니다. 이런 단어가 없는 느슨한 규칙은 스크립트가 보호하지 않으므로 diff를 읽으세요. 스킬은 완전 중복이 아닌데 제거된 줄을 에이전트가 전부 나열하도록 지시합니다.

</details>

<details>
<summary><b>그냥 파일을 지우고 처음부터 쓰면 안 되나요?</b></summary>

그게 맞을 때도 있고, 그럴 때도 감사가 도움이 됩니다. 제약 목록이 반드시 옮겨 가야 하는 부분이기 때문입니다. 하지만 대부분의 파일은 그 정도로 나쁘지 않습니다. 실제 규칙이라는 핵심을, 한때는 유용했던 설명과 예시가 둘러싸고 있을 뿐입니다. 설명을 `references/`로 옮기면 다시 필요한 날을 위해 보관하면서도 나머지 모든 턴에서는 비용이 들지 않습니다.

</details>

<details>
<summary><b>영어가 아닌 파일에서도 동작하나요?</b></summary>

크기 측정과 중복 탐지는 어떤 언어에서도 동작합니다. 서술형 표현 목록과 제약 키워드는 영어이므로, 러시아어나 독일어 규칙은 표시되지도 보호되지도 않습니다. 표현 목록을 추가하는 풀 리퀘스트를 환영합니다. [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

</details>

## 관련 프로젝트

- [token-diet](https://github.com/uniqaiapp/token-diet): 의미를 잃지 않고 프롬프트와 컨텍스트 토큰을 줄입니다. 측정 가능한 규칙, stdlib 추정기, 전후 예시를 제공합니다. skill-shrinker는 같은 아이디어를 지시 파일 자체에 적용한 것입니다.
- [model-router](https://github.com/uniqaiapp/model-router): 작업을 처리할 수 있는 가장 저렴한 모델을 고릅니다. 규칙 표와, 유형·길이·위험도로 작업을 라우팅하는 stdlib 스크립트입니다.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): 러시아어 텍스트에서 AI 티가 나는 군더더기를 걷어냅니다. 흔한 징후를 찾아 다시 쓰는 스킬과 stdlib 스크립트입니다.

## 기여하기

이슈와 풀 리퀘스트를 환영합니다. 변경은 작게 유지하고 PR 설명에 전후 예시를 넣어 주세요.
로컬 검사(`python3 tests/run.py`, 의존성 없음)는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub><a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ko&utm_campaign=skill-shrinker">UniqAI</a> 제작 — Kling 3.0, Veo 3, Flux, Nano Banana, GPT-5/Claude/Gemini/Grok을 앱 하나에서. 저희 스킬을 짧게 유지하려고 만든 도구입니다.</sub>

</div>
