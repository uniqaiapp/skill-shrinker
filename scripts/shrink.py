#!/usr/bin/env python3
"""skill-shrinker: measure, audit and compare agent instruction files.

Works on CLAUDE.md, AGENTS.md, SKILL.md, .cursor/rules/*.mdc or any Markdown
that an agent loads into context. Python 3.9+ standard library only.

Usage
  python3 scripts/shrink.py report  FILE [FILE ...] [--tokens auto|api|estimate] [--md|--json]
  python3 scripts/shrink.py audit   FILE [--max-block N] [--max-section N] [--json]
  python3 scripts/shrink.py compare BEFORE AFTER [--tokens auto|api|estimate] [--md|--json] [--strict]

Token counts
  --tokens api       exact count from Anthropic count_tokens (needs ANTHROPIC_API_KEY)
  --tokens estimate  local heuristic, always labelled "estimate"
  --tokens auto      api when ANTHROPIC_API_KEY is set, otherwise estimate (default)
  SHRINK_MODEL       model id for the API count (default: claude-opus-5-5)

Exit codes
  0 ok · 1 usage or I/O error · 2 `compare --strict` found a lost constraint
"""
import argparse
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

__version__ = "0.1.0"

DEFAULT_MODEL = "claude-opus-5-5"
API_URL = "https://api.anthropic.com/v1/messages/count_tokens"

# --------------------------------------------------------------------------- text basics

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"\(([^)\s]+\.md)\)|`([^`\s]+\.md)`")
WORD_RE = re.compile(r"\w+(?:'\w+)?|\d+|[^\w\s]", re.UNICODE)

CONSTRAINT_RE = re.compile(
    r"\b(must not|must never|must|never|always|do not|don't|shall not|shall|"
    r"required|forbidden|prohibited|only ever|under no circumstances)\b",
    re.I,
)
NEGATION_RE = re.compile(r"\b(must not|must never|do not|don't|never|avoid|no|not|shall not|forbidden|prohibited)\b", re.I)
POLARITY_WORDS_RE = re.compile(
    r"\b(must not|must never|do not|don't|never|avoid|not|no|always|must|should|shall|please|you|we)\b", re.I
)

# Phrases that narrate instead of instruct. Each costs tokens on every turn and tells the agent nothing.
FILLER = [
    "in this document", "in this file", "in this section", "this document describes", "this file describes",
    "this section describes", "this guide will", "we will walk through", "let's", "lets start", "here we",
    "as you can see", "as mentioned above", "as mentioned earlier", "as noted above", "please note that",
    "note that", "it is important to", "it's important to", "it is worth noting", "it's worth noting",
    "keep in mind that", "remember that", "feel free to", "make sure to", "be sure to", "you should always",
    "in order to", "basically", "essentially", "obviously", "of course", "needless to say", "last but not least",
    "at the end of the day", "the following section", "below you will find", "we recommend that you",
    "it is recommended", "going forward", "as a reminder", "for your convenience", "it goes without saying",
]
FILLER_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in FILLER) + r")\b", re.I)


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def split_frontmatter(text: str) -> Tuple[str, str]:
    m = FRONTMATTER_RE.match(text)
    return (m.group(0), text[m.end():]) if m else ("", text)


def fmt_int(n: int) -> str:
    return "{:,}".format(n)


def fmt_pct(before: int, after: int) -> str:
    if before == 0:
        return "n/a"
    d = (after - before) * 100.0 / before
    return ("%+.0f%%" % d) if abs(d) >= 0.5 else "0%"


# --------------------------------------------------------------------------- tokens

def estimate_tokens(text: str) -> int:
    """Local heuristic, deliberately simple and documented in references/token-estimate.md.

    Each word is ~1 token per 6 Latin characters (minimum 1); non-Latin words ~1 token per
    2.5 characters; digit runs ~1 token per 3 digits; every punctuation mark 1 token; each
    run of newlines 1 token. It is an estimate: expect it to be within roughly a fifth of the
    real count on English Markdown, worse on code and non-English text. Use --tokens api for
    exact numbers.
    """
    n = 0
    for m in WORD_RE.finditer(text):
        tok = m.group(0)
        if tok.isdigit():
            n += max(1, math.ceil(len(tok) / 3))
        elif tok[0].isalnum() or tok[0] == "_":
            if all(ord(c) < 128 for c in tok):
                n += max(1, math.ceil(len(tok) / 6))
            else:
                n += max(1, math.ceil(len(tok) / 2.5))
        else:
            n += 1
    n += len(re.findall(r"\n+", text))
    return n


def count_tokens_api(text: str, model: str, api_key: str, timeout: int = 30) -> int:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": text}]}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec: fixed https URL
        data = json.loads(resp.read().decode("utf-8"))
    return int(data["input_tokens"])


class TokenCounter:
    """Picks api or estimate once, then counts consistently for every file in one run."""

    def __init__(self, mode: str = "auto", model: Optional[str] = None):
        self.model = model or os.environ.get("SHRINK_MODEL", DEFAULT_MODEL)
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if mode == "api" and not key:
            raise SystemExit("--tokens api needs ANTHROPIC_API_KEY in the environment")
        self.use_api = (mode == "api") or (mode == "auto" and bool(key))
        self.key = key
        self.label = ("exact, %s" % self.model) if self.use_api else "estimate"

    def count(self, text: str) -> int:
        if not text.strip():
            return 0
        if self.use_api:
            try:
                return count_tokens_api(text, self.model, self.key)
            except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as e:
                raise SystemExit("count_tokens failed (%s); retry with --tokens estimate" % e)
        return estimate_tokens(text)


def measure(text: str, counter: TokenCounter) -> Dict[str, int]:
    return {
        "lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "words": len(text.split()),
        "chars": len(text),
        "tokens": counter.count(text),
    }


# --------------------------------------------------------------------------- line model

class Line:
    __slots__ = ("no", "raw", "kind", "norm", "words", "heading_level", "heading")

    def __init__(self, no: int, raw: str, kind: str):
        self.no = no
        self.raw = raw
        self.kind = kind  # text | heading | code | fence | blank | table
        self.norm = ""
        self.words: List[str] = []
        self.heading_level = 0
        self.heading = ""


def normalize(line: str) -> str:
    s = BULLET_RE.sub("", line.strip())
    s = re.sub(r"[*_`>#]+", "", s)
    s = re.sub(r"[^\w\s'/.-]", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s


def parse_lines(body: str) -> List[Line]:
    out: List[Line] = []
    in_fence = False
    for i, raw in enumerate(body.split("\n"), start=1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            out.append(Line(i, raw, "fence"))
            continue
        if in_fence:
            out.append(Line(i, raw, "code"))
            continue
        if not raw.strip():
            out.append(Line(i, raw, "blank"))
            continue
        hm = HEADING_RE.match(raw)
        if hm:
            ln = Line(i, raw, "heading")
            ln.heading_level = len(hm.group(1))
            ln.heading = hm.group(2).strip()
            out.append(ln)
            continue
        if raw.lstrip().startswith("|"):
            out.append(Line(i, raw, "table"))
            continue
        ln = Line(i, raw, "text")
        ln.norm = normalize(raw)
        ln.words = ln.norm.split()
        out.append(ln)
    return out


def is_rule(ln: Line) -> bool:
    # a bare command line in backticks is not a rule; two commands sharing a script name are not duplicates
    s = BULLET_RE.sub("", ln.raw.strip())
    if s.startswith("`") and s.endswith("`") and s.count("`") == 2:
        return False
    return ln.kind == "text" and len(ln.words) >= 3


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\"'(])")


def constraint_sentences(raw: str) -> List[str]:
    """The sentences of a line that carry a MUST/NEVER/ALWAYS/DO NOT style constraint."""
    s = BULLET_RE.sub("", raw.strip())
    return [x.strip() for x in SENTENCE_RE.split(s) if CONSTRAINT_RE.search(x)]


def constraint_norm(sentence: str) -> str:
    """Normalised form used to check that a constraint survived: filler phrases stripped."""
    return re.sub(r"\s+", " ", FILLER_RE.sub(" ", normalize(sentence))).strip(" ,")


def polarity_key(ln: Line) -> Tuple[str, bool]:
    """Return (subject without polarity words, negated?) so 'always X' and 'never X' collide."""
    negated = bool(NEGATION_RE.search(ln.norm))
    key = POLARITY_WORDS_RE.sub(" ", ln.norm)
    key = re.sub(r"\s+", " ", key).strip()
    return key, negated


def jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


# --------------------------------------------------------------------------- audit

def audit(path: str, text: str, counter: TokenCounter, max_block: int = 15, max_section: int = 40) -> Dict:
    fm, body = split_frontmatter(text)
    offset = fm.count("\n")
    lines = parse_lines(body)
    for ln in lines:
        ln.no += offset

    rules = [ln for ln in lines if is_rule(ln)]

    # 1. constraints: keep verbatim (sentence level, so a rule buried in a paragraph is still found)
    constraints = [(ln, s) for ln in lines if ln.kind == "text" for s in constraint_sentences(ln.raw)]

    # 2. exact duplicates after normalisation
    groups: Dict[str, List[Line]] = {}
    for ln in rules:
        groups.setdefault(ln.norm, []).append(ln)
    duplicates = [g for g in groups.values() if len(g) > 1]
    dup_lines = {ln.no for g in duplicates for ln in g}

    # 3. contradictions: same subject, opposite polarity
    contradictions: List[Tuple[Line, Line]] = []
    by_key: Dict[str, List[Tuple[Line, bool]]] = {}
    for ln in rules:
        key, neg = polarity_key(ln)
        if len(key.split()) >= 2:
            by_key.setdefault(key, []).append((ln, neg))
    for key, items in by_key.items():
        pos = [ln for ln, neg in items if not neg]
        negs = [ln for ln, neg in items if neg]
        for p in pos:
            for n in negs:
                contradictions.append((p, n))
    contra_pairs = {frozenset((p.no, n.no)) for p, n in contradictions}

    # 4. near-duplicates (same meaning, different wording)
    near: List[Tuple[Line, Line, float]] = []
    cand = [ln for ln in rules if len(ln.words) >= 4 and ln.no not in dup_lines]
    for i in range(len(cand)):
        for j in range(i + 1, len(cand)):
            a, b = cand[i], cand[j]
            if a.norm == b.norm or frozenset((a.no, b.no)) in contra_pairs:
                continue
            sim = jaccard(a.words, b.words)
            if sim >= 0.6:
                near.append((a, b, round(sim, 2)))

    # 5. narration and filler
    narration = [(ln, FILLER_RE.search(ln.raw).group(1)) for ln in lines if ln.kind == "text" and FILLER_RE.search(ln.raw)]

    # 6. long code blocks
    blocks: List[Tuple[int, int, int]] = []
    start = None
    for ln in lines:
        if ln.kind == "fence":
            if start is None:
                start = ln.no
            else:
                length = ln.no - start - 1
                if length > max_block:
                    blocks.append((start, ln.no, length))
                start = None

    # 7. long sections, empty sections, repeated headings
    sections: List[Tuple[Line, int, int]] = []  # heading, end line, content lines
    heads = [ln for ln in lines if ln.kind == "heading"]
    for idx, h in enumerate(heads):
        end = lines[-1].no
        for nxt in heads[idx + 1:]:
            if nxt.heading_level <= h.heading_level:
                end = nxt.no - 1
                break
        content = [ln for ln in lines if h.no < ln.no <= end and ln.kind not in ("blank", "heading")]
        sections.append((h, end, len(content)))
    long_sections = [(h, end, n) for h, end, n in sections if n > max_section and h.heading_level > 1]
    empty_sections = [h for h, end, n in sections if n == 0 and not any(
        (x.no > h.no and x.no <= end and x.kind == "heading") for x in lines)]
    seen: Dict[str, Line] = {}
    repeated_headings: List[Tuple[Line, Line]] = []
    for h in heads:
        k = h.heading.lower()
        if k in seen:
            repeated_headings.append((seen[k], h))
        else:
            seen[k] = h

    # 8. long tables
    tables: List[Tuple[int, int, int]] = []
    tstart = None
    prev_table = False
    for ln in lines + [Line(lines[-1].no + 1 if lines else 1, "", "blank")]:
        if ln.kind == "table":
            if not prev_table:
                tstart = ln.no
            prev_table = True
        else:
            if prev_table and tstart is not None:
                rows = ln.no - tstart - 2  # minus header and separator
                if rows > 12:
                    tables.append((tstart, ln.no - 1, rows))
            prev_table = False

    flagged = set()
    flagged.update(dup_lines)
    flagged.update(ln.no for a, b, _ in near for ln in (a, b))
    flagged.update(ln.no for ln, _ in narration)
    for s, e, _ in blocks:
        flagged.update(range(s + 1 + max_block, e))
    for h, e, _ in long_sections:
        flagged.update(x.no for x in lines if h.no < x.no <= e and x.kind not in ("blank", "heading"))
    for s, e, _ in tables:
        flagged.update(range(s + 2 + 12, e + 1))

    return {
        "file": path,
        "size": dict(measure(text, counter), token_label=counter.label),
        "constraints": [{"line": ln.no, "text": s} for ln, s in constraints],
        "duplicates": [[{"line": ln.no, "text": ln.raw.strip()} for ln in g] for g in duplicates],
        "near_duplicates": [{"a": a.no, "b": b.no, "similarity": s, "a_text": a.raw.strip(), "b_text": b.raw.strip()} for a, b, s in near],
        "contradictions": [{"a": p.no, "b": n.no, "a_text": p.raw.strip(), "b_text": n.raw.strip()} for p, n in contradictions],
        "narration": [{"line": ln.no, "phrase": ph, "text": ln.raw.strip()} for ln, ph in narration],
        "long_code_blocks": [{"start": s, "end": e, "lines": n} for s, e, n in blocks],
        "long_sections": [{"heading": h.raw.strip(), "start": h.no, "end": e, "content_lines": n} for h, e, n in long_sections],
        "empty_sections": [{"heading": h.raw.strip(), "line": h.no} for h in empty_sections],
        "repeated_headings": [{"first": a.no, "again": b.no, "heading": b.heading} for a, b in repeated_headings],
        "long_tables": [{"start": s, "end": e, "rows": n} for s, e, n in tables],
        "flagged_lines": len(flagged),
        "thresholds": {"max_block": max_block, "max_section": max_section, "max_table_rows": 12},
    }


def clip(s: str, n: int = 88) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def render_audit(a: Dict) -> str:
    z = a["size"]
    out = []
    out.append("skill-shrinker audit: %s" % a["file"])
    out.append("  %s lines · %s words · %s chars · %s tokens (%s)" % (
        fmt_int(z["lines"]), fmt_int(z["words"]), fmt_int(z["chars"]), fmt_int(z["tokens"]), z["token_label"]))
    out.append("")

    def section(title: str, count: int, unit: str = ""):
        out.append("%-28s %d%s" % (title.upper(), count, (" " + unit) if unit else ""))

    section("constraints (keep verbatim)", len(a["constraints"]))
    for c in a["constraints"]:
        out.append("  L%-5d %s" % (c["line"], clip(c["text"])))
    out.append("")

    section("duplicate lines", len(a["duplicates"]), "groups")
    for g in a["duplicates"]:
        out.append("  %s" % ", ".join("L%d" % x["line"] for x in g))
        out.append("      %s" % clip(g[0]["text"]))
    out.append("")

    section("near-duplicates", len(a["near_duplicates"]), "pairs")
    for p in a["near_duplicates"]:
        out.append("  L%d ~ L%d  (%.2f)" % (p["a"], p["b"], p["similarity"]))
        out.append("      %s" % clip(p["a_text"]))
        out.append("      %s" % clip(p["b_text"]))
    out.append("")

    section("contradictions", len(a["contradictions"]))
    for p in a["contradictions"]:
        out.append("  L%d vs L%d" % (p["a"], p["b"]))
        out.append("      %s" % clip(p["a_text"]))
        out.append("      %s" % clip(p["b_text"]))
    out.append("")

    section("narration / filler", len(a["narration"]), "lines")
    for n in a["narration"]:
        out.append("  L%-5d [%s] %s" % (n["line"], n["phrase"], clip(n["text"], 70)))
    out.append("")

    section("long code blocks", len(a["long_code_blocks"]), "(> %d lines)" % a["thresholds"]["max_block"])
    for b in a["long_code_blocks"]:
        out.append("  L%d-L%d  %d lines → keep the shortest working example, move the rest to references/" % (b["start"], b["end"], b["lines"]))
    out.append("")

    section("long sections", len(a["long_sections"]), "(> %d content lines)" % a["thresholds"]["max_section"])
    for s in a["long_sections"]:
        out.append("  %s  L%d-L%d  %d lines → references/%s.md + a one-line pointer" % (
            clip(s["heading"], 40), s["start"], s["end"], s["content_lines"], slug(s["heading"])))
    out.append("")

    section("long tables", len(a["long_tables"]), "(> %d rows)" % a["thresholds"]["max_table_rows"])
    for t in a["long_tables"]:
        out.append("  L%d-L%d  %d rows → references/" % (t["start"], t["end"], t["rows"]))
    out.append("")

    section("empty sections", len(a["empty_sections"]))
    for e in a["empty_sections"]:
        out.append("  L%-5d %s" % (e["line"], clip(e["heading"])))
    out.append("")

    section("repeated headings", len(a["repeated_headings"]))
    for r in a["repeated_headings"]:
        out.append("  L%d again at L%d  %s" % (r["first"], r["again"], clip(r["heading"])))
    out.append("")

    out.append("Lines touched by at least one finding: %d of %d" % (a["flagged_lines"], z["lines"]))
    out.append("Next: edit by hand (SKILL.md rules), then: python3 scripts/shrink.py compare BEFORE AFTER")
    return "\n".join(out) + "\n"


def slug(heading: str) -> str:
    s = re.sub(r"[#*`]+", "", heading).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "section"


# --------------------------------------------------------------------------- report

def report(paths: List[str], counter: TokenCounter) -> Dict:
    rows = []
    for p in paths:
        rows.append(dict(file=p, **measure(read_text(p), counter)))
    total = {k: sum(r[k] for r in rows) for k in ("lines", "words", "chars", "tokens")}
    return {"token_label": counter.label, "files": rows, "total": total}


def render_report(r: Dict, md: bool = False) -> str:
    rows = r["files"]
    head = ["file", "lines", "words", "chars", "tokens (%s)" % r["token_label"]]
    body = [[x["file"], fmt_int(x["lines"]), fmt_int(x["words"]), fmt_int(x["chars"]), fmt_int(x["tokens"])] for x in rows]
    if len(rows) > 1:
        t = r["total"]
        body.append(["total", fmt_int(t["lines"]), fmt_int(t["words"]), fmt_int(t["chars"]), fmt_int(t["tokens"])])
    return table(head, body, md)


def table(head: List[str], body: List[List[str]], md: bool) -> str:
    if md:
        lines = ["| " + " | ".join(head) + " |", "|:--|" + "--:|" * (len(head) - 1)]
        for row in body:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines) + "\n"
    widths = [max(len(str(r[i])) for r in [head] + body) for i in range(len(head))]
    lines = []
    for ri, row in enumerate([head] + body):
        cells = [row[0].ljust(widths[0])] + [str(c).rjust(widths[i]) for i, c in enumerate(row) if i > 0]
        lines.append("  ".join(cells).rstrip())
        if ri == 0:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- compare

def referenced_files(after_path: str, after_text: str) -> List[str]:
    base = os.path.dirname(os.path.abspath(after_path))
    found: List[str] = []
    for m in LINK_RE.finditer(after_text):
        rel = m.group(1) or m.group(2)
        if rel.startswith(("http://", "https://")):
            continue
        p = os.path.normpath(os.path.join(base, rel))
        if os.path.isfile(p) and p != os.path.abspath(after_path) and p not in found:
            found.append(p)
    return found


def constraint_norms(text: str) -> List[Tuple[str, str]]:
    _, body = split_frontmatter(text)
    out = []
    for ln in parse_lines(body):
        if ln.kind == "text":
            for s in constraint_sentences(ln.raw):
                out.append((constraint_norm(s), s))
    return out


def text_norm(text: str) -> str:
    return " " + " ".join(constraint_norm(l) for l in text.split("\n") if l.strip()) + " "


def compare(before: str, after: str, counter: TokenCounter) -> Dict:
    tb, ta = read_text(before), read_text(after)
    mb, ma = measure(tb, counter), measure(ta, counter)
    refs = referenced_files(after, ta)
    ref_texts = {p: read_text(p) for p in refs}
    mr = {k: sum(measure(t, counter)[k] for t in ref_texts.values()) for k in ("lines", "words", "chars", "tokens")} if refs else None

    # a constraint counts as kept when its normalised sentence appears anywhere in AFTER
    after_text_norm = text_norm(ta)
    ref_norm = " ".join(text_norm(t) for t in ref_texts.values())
    kept, in_refs, lost = [], [], []
    for norm, raw in constraint_norms(tb):
        if norm and norm in after_text_norm:
            kept.append(raw)
        elif norm and norm in ref_norm:
            in_refs.append(raw)
        else:
            lost.append(raw)
    base = os.path.dirname(os.path.abspath(after))
    return {
        "token_label": counter.label,
        "before": dict(file=before, **mb),
        "after": dict(file=after, **ma),
        "references": dict(files=[os.path.relpath(p, base) for p in refs], **mr) if mr else None,
        "constraints": {"total": len(kept) + len(in_refs) + len(lost), "kept": kept, "moved_to_references": in_refs, "lost": lost},
    }


def render_compare(c: Dict, md: bool = False) -> str:
    b, a, r = c["before"], c["after"], c["references"]
    head = ["", b["file"], a["file"], "change"]
    rows = []
    for k, label in (("lines", "lines"), ("words", "words"), ("chars", "chars"), ("tokens", "tokens (%s)" % c["token_label"])):
        rows.append([label, fmt_int(b[k]), fmt_int(a[k]), fmt_pct(b[k], a[k])])
    out = table(head, rows, md)
    if r:
        out += "\n"
        out += ("Moved to references (loaded only when the agent needs them): %s\n" % ", ".join(r["files"]))
        out += ("  %s lines · %s words · %s tokens (%s)\n" % (fmt_int(r["lines"]), fmt_int(r["words"]), fmt_int(r["tokens"]), c["token_label"]))
        out += ("  after + references vs before, tokens: %s\n" % fmt_pct(b["tokens"], a["tokens"] + r["tokens"]))
    k = c["constraints"]
    out += "\n"
    out += "Constraint lines (MUST / NEVER / ALWAYS / DO NOT): %d in before, %d kept verbatim, %d only in references, %d lost\n" % (
        k["total"], len(k["kept"]), len(k["moved_to_references"]), len(k["lost"]))
    for raw in k["moved_to_references"]:
        out += "  only in references: %s\n" % clip(raw)
    for raw in k["lost"]:
        out += "  LOST: %s\n" % clip(raw)
    return out


# --------------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shrink.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version="skill-shrinker %s" % __version__)
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("--tokens", choices=["auto", "api", "estimate"], default="auto", help="token source (default auto)")
        sp.add_argument("--model", default=None, help="model id for --tokens api (default $SHRINK_MODEL or %s)" % DEFAULT_MODEL)
        sp.add_argument("--json", action="store_true", help="machine-readable output")

    sp = sub.add_parser("report", help="size of one or more files")
    sp.add_argument("files", nargs="+")
    sp.add_argument("--md", action="store_true", help="Markdown table")
    common(sp)

    sp = sub.add_parser("audit", help="flag duplicates, contradictions, narration, long blocks and sections")
    sp.add_argument("file")
    sp.add_argument("--max-block", type=int, default=15, help="code block lines before it is flagged (default 15)")
    sp.add_argument("--max-section", type=int, default=40, help="content lines per section before it is flagged (default 40)")
    common(sp)

    sp = sub.add_parser("compare", help="before/after table and constraint preservation check")
    sp.add_argument("before")
    sp.add_argument("after")
    sp.add_argument("--md", action="store_true", help="Markdown table")
    sp.add_argument("--strict", action="store_true", help="exit 2 if a constraint line from BEFORE is missing from AFTER and its references")
    common(sp)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return 1
    try:
        counter = TokenCounter(args.tokens, args.model)
        if args.cmd == "report":
            r = report(args.files, counter)
            sys.stdout.write(json.dumps(r, indent=2) + "\n" if args.json else render_report(r, args.md))
        elif args.cmd == "audit":
            a = audit(args.file, read_text(args.file), counter, args.max_block, args.max_section)
            sys.stdout.write(json.dumps(a, indent=2, ensure_ascii=False) + "\n" if args.json else render_audit(a))
        elif args.cmd == "compare":
            c = compare(args.before, args.after, counter)
            sys.stdout.write(json.dumps(c, indent=2, ensure_ascii=False) + "\n" if args.json else render_compare(c, args.md))
            if args.strict and c["constraints"]["lost"]:
                return 2
    except OSError as e:
        sys.stderr.write("shrink.py: %s\n" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
