"""Unit tests for the heuristics in scripts/shrink.py: each one with a document that triggers it and
one that must not."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import shrink  # noqa: E402

EST = shrink.TokenCounter("estimate")


def audit(text, **kw):
    return shrink.audit("doc.md", text, EST, **kw)


class Tokens(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(shrink.estimate_tokens(""), 0)
        self.assertEqual(EST.count("   \n"), 0)

    def test_monotonic_in_length(self):
        a = shrink.estimate_tokens("Run the tests before every commit.")
        b = shrink.estimate_tokens("Run the tests before every commit. Then open a pull request.")
        self.assertGreater(b, a)

    def test_rough_order_of_magnitude(self):
        text = ("Use named exports. Do not use default exports. Keep files small. " * 40)
        est = shrink.estimate_tokens(text)
        # ~4 chars/token is the common rule of thumb; stay within a factor of two of it
        self.assertTrue(len(text) / 8 < est < len(text) / 2, est)

    def test_non_latin_counts_more_per_word(self):
        self.assertGreater(shrink.estimate_tokens("Всегда запускайте тесты"), shrink.estimate_tokens("Always run tests"))

    def test_label(self):
        self.assertEqual(EST.label, "estimate")

    def test_api_mode_requires_key(self):
        old = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with self.assertRaises(SystemExit):
                shrink.TokenCounter("api")
        finally:
            if old is not None:
                os.environ["ANTHROPIC_API_KEY"] = old


class Measure(unittest.TestCase):
    def test_counts(self):
        m = shrink.measure("a b\nc\n", EST)
        self.assertEqual((m["lines"], m["words"], m["chars"]), (2, 3, 6))

    def test_frontmatter_split(self):
        fm, body = shrink.split_frontmatter("---\nname: x\n---\n# T\n")
        self.assertEqual(fm, "---\nname: x\n---\n")
        self.assertEqual(body, "# T\n")
        self.assertEqual(shrink.split_frontmatter("# T\n"), ("", "# T\n"))


class Normalise(unittest.TestCase):
    def test_bullets_case_and_markup_ignored(self):
        self.assertEqual(shrink.normalize("- **Always** run `pnpm test`."), shrink.normalize("1. always run pnpm test"))

    def test_constraint_sentences(self):
        s = shrink.constraint_sentences("Obviously errors happen. Never swallow them silently. Log them.")
        self.assertEqual(s, ["Never swallow them silently."])
        self.assertEqual(shrink.constraint_sentences("Prefer named exports."), [])

    def test_constraint_norm_strips_filler(self):
        self.assertEqual(shrink.constraint_norm("Remember that handlers must not throw."), shrink.constraint_norm("Handlers must not throw."))


class Findings(unittest.TestCase):
    def test_exact_duplicate(self):
        a = audit("# T\n\n- Run tests before every commit.\n\n## Git\n\n- run tests before every commit\n")
        self.assertEqual(len(a["duplicates"]), 1)
        self.assertEqual([x["line"] for x in a["duplicates"][0]], [3, 7])

    def test_no_false_duplicate_on_short_lines(self):
        a = audit("# T\n\n- Yes.\n- Yes.\n")
        self.assertEqual(a["duplicates"], [])

    def test_near_duplicate(self):
        a = audit("# T\n\n- Prefer named exports over default exports.\n- Prefer named exports to default exports.\n")
        self.assertEqual(len(a["near_duplicates"]), 1)
        self.assertGreaterEqual(a["near_duplicates"][0]["similarity"], 0.6)

    def test_bare_command_lines_are_not_rules(self):
        a = audit("# T\n\n`python3 scripts/shrink.py report CLAUDE.md`\n`python3 scripts/shrink.py audit CLAUDE.md`\n")
        self.assertEqual(a["near_duplicates"], [])

    def test_contradiction(self):
        a = audit("# T\n\n- Always use tabs for indentation.\n\n## Later\n\n- Never use tabs for indentation.\n")
        self.assertEqual(len(a["contradictions"]), 1)
        self.assertEqual((a["contradictions"][0]["a"], a["contradictions"][0]["b"]), (3, 7))
        self.assertEqual(a["near_duplicates"], [], "a contradiction is not also reported as a near-duplicate")

    def test_no_contradiction_for_different_subjects(self):
        a = audit("# T\n\n- Always use tabs for indentation.\n- Never use yarn for installs.\n")
        self.assertEqual(a["contradictions"], [])

    def test_narration(self):
        a = audit("# T\n\nIn this document we will explain the rules.\n\n- Run tests.\n")
        self.assertEqual([n["line"] for n in a["narration"]], [3])

    def test_long_code_block_and_threshold(self):
        code = "```bash\n" + "echo x\n" * 20 + "```\n"
        self.assertEqual(len(audit("# T\n\n" + code)["long_code_blocks"]), 1)
        self.assertEqual(len(audit("# T\n\n" + code, max_block=25)["long_code_blocks"]), 0)

    def test_code_lines_are_not_rules(self):
        a = audit("# T\n\n```\nalways use tabs here\nnever use tabs here\n```\n")
        self.assertEqual(a["contradictions"], [])
        self.assertEqual(a["constraints"], [])

    def test_long_section_skips_h1(self):
        body = "".join("- rule number %d is here\n" % i for i in range(45))
        a = audit("# T\n\n" + body)
        self.assertEqual(a["long_sections"], [])
        a = audit("# T\n\n## S\n\n" + body)
        self.assertEqual(len(a["long_sections"]), 1)
        self.assertEqual(a["long_sections"][0]["heading"], "## S")

    def test_empty_section_and_repeated_heading(self):
        a = audit("# T\n\n## Setup\n\ntext\n\n## Deploy\n\n## Setup\n\nmore\n")
        self.assertEqual([e["heading"] for e in a["empty_sections"]], ["## Deploy"])
        self.assertEqual(len(a["repeated_headings"]), 1)

    def test_parent_with_only_subsections_is_not_empty(self):
        a = audit("# T\n\n## Parent\n\n### Child\n\ntext\n")
        self.assertEqual(a["empty_sections"], [])

    def test_long_table(self):
        rows = "| a | b |\n|---|---|\n" + "".join("| r%d | v |\n" % i for i in range(13))
        self.assertEqual(len(audit("# T\n\n" + rows)["long_tables"]), 1)
        rows = "| a | b |\n|---|---|\n" + "".join("| r%d | v |\n" % i for i in range(5))
        self.assertEqual(audit("# T\n\n" + rows)["long_tables"], [])

    def test_frontmatter_offsets_line_numbers(self):
        a = audit("---\nname: x\n---\n# T\n\nNote that this is filler.\n")
        self.assertEqual(a["narration"][0]["line"], 6)

    def test_slug(self):
        self.assertEqual(shrink.slug("## Local setup (from scratch)"), "local-setup-from-scratch")


class Compare(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.dir, "references"))

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_kept_moved_lost(self):
        before = self.write("before.md", "# T\n\n- You MUST run tests.\n- Never push to main.\n- Always squash.\n- Do not use yarn.\n")
        after = self.write("after.md", "# T\n\n- Rules: you MUST run tests.\n- Never push to main.\n\nSee [setup](references/setup.md).\n")
        self.write("references/setup.md", "Always squash.\n")
        c = shrink.compare(before, after, EST)
        k = c["constraints"]
        self.assertEqual(k["total"], 4)
        self.assertEqual(len(k["kept"]), 2)
        self.assertEqual(k["moved_to_references"], ["Always squash."])
        self.assertEqual(k["lost"], ["Do not use yarn."])
        self.assertEqual(c["references"]["files"], ["references/setup.md"])

    def test_missing_reference_is_ignored(self):
        before = self.write("b.md", "- Never push.\n")
        after = self.write("a.md", "- Never push.\n\nSee [x](references/missing.md).\n")
        c = shrink.compare(before, after, EST)
        self.assertIsNone(c["references"])
        self.assertEqual(c["constraints"]["lost"], [])

    def test_pct(self):
        self.assertEqual(shrink.fmt_pct(200, 100), "-50%")
        self.assertEqual(shrink.fmt_pct(100, 100), "0%")
        self.assertEqual(shrink.fmt_pct(0, 5), "n/a")


if __name__ == "__main__":
    unittest.main()
