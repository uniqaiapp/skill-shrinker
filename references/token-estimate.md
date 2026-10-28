# Token counting in skill-shrinker

Two modes, chosen once per run and printed in every table header as `tokens (estimate)` or `tokens (exact, <model>)`.

## Exact: Anthropic `count_tokens`

When `ANTHROPIC_API_KEY` is set and `--tokens` is `auto` (default) or `api`, the script sends the file as one user message to `POST https://api.anthropic.com/v1/messages/count_tokens` and reports `input_tokens`. The model is `claude-opus-5-5` unless `SHRINK_MODEL` or `--model` says otherwise; counts are model-specific, so use the model you actually run the skill on. The request contains the whole file; use `--tokens estimate` for anything that must not leave the machine. One request per file, no retries, 30 second timeout; on failure the script stops with a message instead of silently falling back, so a published "exact" number is never secretly an estimate.

Other vendors have equivalent endpoints; the script does not call them. If you need another tokenizer, run it yourself on the same files and label the column.

## Estimate: the local heuristic

`estimate_tokens()` in `scripts/shrink.py`:

| Piece of text | Counted as |
|---|---|
| Latin-script word (letters, digits, underscore, apostrophe) | 1 token per 6 characters, rounded up, minimum 1 |
| Non-Latin word (Cyrillic, CJK, ...) | 1 token per 2.5 characters, rounded up |
| Run of digits | 1 token per 3 digits, rounded up |
| Any other non-space character (punctuation, symbols, Markdown markup) | 1 token |
| Run of newlines | 1 token |

Why these numbers: subword tokenizers merge common short words into one token and split long or rare words into several; punctuation and Markdown markup are usually one token each; non-Latin scripts get far fewer characters per token. The heuristic was tuned to land near the common "about four characters per token" rule on English Markdown with code blocks, while still moving in the right direction on code-heavy and non-English files. It is not calibrated against any specific tokenizer and is deliberately simple so it can be read in ten lines.

What to expect: the heuristic is not calibrated against any tokenizer, so there is no measured error bound to quote; on code blocks and tables it tends to undercount, and on Russian or CJK text the error is larger than on English prose. Relative changes (before vs after on the same kind of text) are more reliable than absolute values, which is why `compare` is the number that matters.

Rules for publishing a number:

1. Say which mode produced it. The script prints the label; copy it.
2. If it is an estimate, call it an estimate in the sentence, not in a footnote.
3. For a README or a blog post, re-run with `--tokens api` and publish the exact figure with the model name.
