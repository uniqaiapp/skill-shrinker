<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="skill-shrinker by UniqAI" src="assets/banner.svg" width="1280" height="320">
</picture>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Made by UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-pt-br&utm_campaign=skill-shrinker)

# skill-shrinker: compacte SKILL.md, AGENTS.md e regras do Cursor

**Encolha qualquer SKILL.md ou arquivo de instruções de agente: mede o tamanho, move o material longo para references e mantém os gatilhos intactos.**

[Início rápido](#início-rápido) · [Como funciona](#como-funciona) · [Exemplos](#exemplos) · [Instalação](#instalação) · [FAQ](#faq)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · Português (BR) · [日本語](README.ja.md) · [한국어](README.ko.md)

O skill-shrinker compacta arquivos `CLAUDE.md`, `AGENTS.md`, `SKILL.md` e `.cursor/rules` para que o Claude Code, o Cursor e o Codex carreguem menos tokens a cada turno. Ele é uma skill (o procedimento de reescrita) mais um script Python sem dependências que encontra regras duplicadas, contradições, narração, exemplos longos e seções mortas, informa os tokens antes e depois e confere se toda frase com MUST / NEVER / ALWAYS / DO NOT sobreviveu à reescrita. Toda instrução fica; o enchimento vai embora.

| **Auditoria com número de linha** | **Reescrita por regra, não por gosto** | **Prova de que nada se perdeu** |
|:---|:---|:---|
| Duplicatas, quase duplicatas, contradições, frases de enchimento, blocos de código com mais de 15 linhas, seções com mais de 40 linhas, seções vazias. | Onze regras ordenadas: restrições ao pé da letra, sobreposições mescladas, narração fora, um exemplo por conceito, detalhe raro em `references/`. | `compare` imprime a tabela antes/depois e lista cada frase de restrição como mantida, movida para references ou perdida. `--strict` falha o CI em caso de perda. |

## Início rápido

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
python3 ~/.claude/skills/skill-shrinker/scripts/shrink.py audit CLAUDE.md
```

Você recebe uma lista de achados com número de linha e uma linha de tamanho. Depois, no Claude Code: `/skill-shrinker CLAUDE.md` (ou só "este CLAUDE.md está muito longo") e a skill reescreve o arquivo ao lado do original, roda `compare` e relata o que foi movido, o que foi removido e o que contradiz o quê.

## Demo

<img alt="skill-shrinker demo: audit of a 188-line CLAUDE.md, then compare before and after" src="assets/demo.svg" width="820">

A transcrição é uma execução resumida dos comandos de [`examples/README.md`](examples/README.md) sobre `examples/claude-md/`.

## Como funciona

1. **Medir.** `shrink.py report FILE` imprime linhas, palavras, caracteres e tokens. Os tokens são exatos (`count_tokens` da Anthropic, modelo indicado no cabeçalho) quando `ANTHROPIC_API_KEY` está definida; caso contrário, é uma estimativa local, rotulada como tal. Nada sai da máquina a menos que a chave esteja definida; `--tokens estimate` força o modo offline.
2. **Auditar.** `shrink.py audit FILE` trabalha com linhas e frases: duplicatas exatas após normalização, quase duplicatas por sobreposição de palavras, contradições ("always X" contra "never X" sobre as mesmas palavras), uma lista de frases de narração, blocos de código longos, seções longas, tabelas longas, seções vazias, títulos repetidos e as frases de restrição que precisam sobreviver.
3. **Reescrever.** O agente (ou você) aplica as regras de [`SKILL.md`](SKILL.md): restrições idênticas byte a byte, duplicatas fora, sobreposições mescladas, contradições relatadas em vez de resolvidas em silêncio, narração apagada, prosa convertida em imperativos, um exemplo por conceito, setup e troubleshooting movidos para `references/` com um ponteiro de uma linha, frontmatter e frases de gatilho intocados.
4. **Verificar.** `shrink.py compare BEFORE AFTER` imprime a tabela, soma os arquivos referenciados para que a economia seja honesta sobre onde os bytes foram parar e confere cada restrição. As perdidas são impressas com `LOST:`; `--strict` sai com código 2.

Na amostra incluída (`examples/claude-md`, tokens estimados, comando em [`examples/README.md`](examples/README.md)):

|  | before/CLAUDE.md | after/CLAUDE.md | variação |
|:--|--:|--:|--:|
| linhas | 188 | 54 | -71% |
| palavras | 1,345 | 486 | -64% |
| caracteres | 8,413 | 3,169 | -62% |
| tokens (estimativa) | 2,468 | 979 | -60% |

Os dois arquivos de referência que absorveram o script de setup e o exemplo de handler somam 998 tokens estimados, então o conjunto inteiro ficou 20% menor que o original e a parte carregada a cada turno ficou 60% menor. 23 frases de restrição entraram, 21 mantidas ao pé da letra, 1 só em references, 1 perdida de propósito (o lado perdedor de uma contradição tabs vs. espaços). Esses números são o que `scripts/shrink.py` imprime sobre os arquivos de `examples/`; os testes falham se eles divergirem.

```
scripts/shrink.py   report | audit | compare      Python 3.9+, stdlib only
SKILL.md            the procedure and the eleven rewrite rules
references/         playbook with before/after snippets, token estimate notes
examples/           two before/after pairs with committed outputs
```

## Exemplos

<details>
<summary><b>Uma regra enterrada em narração: antes → depois</b></summary>

**Antes**

```text
Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert
failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either
rethrow, or log it with `logger.error` and return a typed failure.
```

**Depois**

```text
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError`
  (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with
  `logger.error` and return a typed failure.
```

A frase de restrição é idêntica byte a byte; o `compare` a encontra. A narração ("Obviously ... should be handled") sumiu.

</details>

<details>
<summary><b>Uma contradição, relatada e não adivinhada</b></summary>

```text
CONTRADICTIONS               1
  L39 vs L185
      - Always use tabs for indentation.
      - Never use tabs for indentation.
```

A skill não escolhe um lado. Ela lista o par e pergunta; em uma execução sem supervisão, mantém o lado apoiado pelas evidências ao redor, e o `compare` mostra o outro como `LOST:`, para que a decisão fique registrada.

</details>

<details>
<summary><b>Gatilhos sobrepostos em um SKILL.md</b></summary>

**Antes**

```text
- The user asks what changed between two tags.
- The user wants to know what shipped since the last release.
- The user asks what changed between two tags or two commits.
```

**Depois**

```text
- What changed between two tags or commits, or since the last release.
```

A união das palavras de gatilho foi preservada, com duas linhas a menos. Par completo: [`examples/skill-md/`](examples/skill-md/).

</details>

## Instalação

Funciona com qualquer agente que leia arquivos de instruções. Escolha o seu. Requisitos: Python 3.9+. Nenhum pacote para instalar.

<details open>
<summary><b>Claude Code</b> (como skill)</summary>

```bash
git clone https://github.com/uniqaiapp/skill-shrinker ~/.claude/skills/skill-shrinker
```
Depois, no Claude Code, digite `/skill-shrinker` ou apenas descreva a tarefa; a skill dispara pela própria descrição.
Local ao projeto em vez de global: clone em `.claude/skills/skill-shrinker` dentro do seu projeto.

Diretório Agent Skills: `npx skills add uniqaiapp/skill-shrinker`.

</details>

<details>
<summary><b>Claude Code</b> (como plugin, quando o marketplace uniqaiapp for publicado)</summary>

```
/plugin marketplace add uniqaiapp/skills
/plugin install skill-shrinker@uniqaiapp
```

</details>

<details>
<summary><b>Cursor</b></summary>

Copie [`SKILL.md`](SKILL.md), `scripts/` e [`.cursor/rules/skill-shrinker.mdc`](.cursor/rules/skill-shrinker.mdc) para o seu projeto. O arquivo de regra incorpora a skill.

</details>

<details>
<summary><b>Codex / qualquer agente que leia AGENTS.md</b></summary>

Copie `SKILL.md` e `scripts/` para `.agents/skills/skill-shrinker/` e adicione o trecho de [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) ao seu `AGENTS.md`.

</details>

<details>
<summary><b>Sem agente</b></summary>

Todo comando roda sozinho: `python3 scripts/shrink.py --help`. As regras de `SKILL.md` funcionam bem como checklist para um editor humano.

</details>

## FAQ

<details>
<summary><b>Ele edita meu arquivo automaticamente?</b></summary>

O script nunca escreve nos seus arquivos; ele imprime. A skill grava a reescrita em um arquivo novo ao lado do original (por exemplo `CLAUDE.shrunk.md`), a menos que você peça edição no próprio arquivo, então você sempre tem um diff.

</details>

<details>
<summary><b>Quão preciso é o número de tokens?</b></summary>

Com `ANTHROPIC_API_KEY` definida, é a contagem exata do `count_tokens` da Anthropic para o modelo indicado na saída (padrão `claude-opus-5-5`, substitua com `SHRINK_MODEL`). Sem chave, é uma heurística documentada ([`references/token-estimate.md`](references/token-estimate.md)), não calibrada contra nenhum tokenizador, então trate os valores absolutos como aproximados, compare apenas números produzidos do mesmo jeito e espere um erro maior em código e em texto não latino. Toda tabela diz `estimate` quando é isso que ela é.

</details>

<details>
<summary><b>Ele vai mudar o significado das minhas instruções?</b></summary>

É para isso que serve a verificação de restrições. Toda frase com MUST, NEVER, ALWAYS, DO NOT e palavras parecidas é conferida entre o original e a reescrita depois de remover o enchimento; encurtar uma delas conta como perdê-la. Regras brandas sem essas palavras não são protegidas pelo script, então leia o diff. A skill instrui o agente a listar toda linha removida que não era uma duplicata exata.

</details>

<details>
<summary><b>Por que não simplesmente apagar o arquivo e começar do zero?</b></summary>

Às vezes isso é o certo, e a auditoria ajuda aí também: a lista de restrições é a parte que você precisa levar junto. A maioria dos arquivos não está tão ruim; eles têm um núcleo de regras reais envolto em explicações e exemplos que um dia foram úteis. Mover as explicações para `references/` as guarda para o dia em que forem necessárias de novo, a custo zero em todos os outros turnos.

</details>

<details>
<summary><b>Funciona com arquivos que não estão em inglês?</b></summary>

A medição de tamanho e a detecção de duplicatas funcionam em qualquer idioma. A lista de frases de narração e as palavras-chave de restrição são em inglês, então regras em russo ou alemão não são sinalizadas nem protegidas. Pull requests com listas de frases são bem-vindos; veja [CONTRIBUTING.md](CONTRIBUTING.md).

</details>

## Relacionados

- [token-diet](https://github.com/uniqaiapp/token-diet): reduza tokens de prompt e de contexto sem perder significado, com regras mensuráveis, um estimador em stdlib e exemplos antes/depois. O skill-shrinker é a mesma ideia aplicada aos próprios arquivos de instruções.
- [model-router](https://github.com/uniqaiapp/model-router): escolha o modelo mais barato que dá conta da tarefa, com uma tabela de regras e um script em stdlib que roteia tarefas por tipo, tamanho e risco.
- [deslop-ru](https://github.com/uniqaiapp/deslop-ru): remova o enchimento com cara de IA de textos em russo, uma skill mais um script em stdlib que sinaliza e reescreve os vícios de sempre.

## Contribuindo

Issues e pull requests são bem-vindos. Mantenha as mudanças pequenas e inclua um exemplo antes/depois na descrição do PR.
Veja [CONTRIBUTING.md](CONTRIBUTING.md) para as verificações locais (`python3 tests/run.py`, sem dependências).

## Licença

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Feito pela <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-pt-br&utm_campaign=skill-shrinker">UniqAI</a> — Kling 3.0, Veo 3, Flux, Nano Banana e GPT-5/Claude/Gemini/Grok em um só app. Escrevemos isto para manter as nossas próprias skills curtas.</sub>

</div>
