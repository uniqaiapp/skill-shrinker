"""Every script answers --help, and every committed example output is reproduced byte-for-byte.
That is how the numbers in README stay honest: they are whatever these commands print."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join("scripts", "shrink.py")

# (committed output, argv) pairs; also listed in examples/README.md
CASES = [
    ("examples/claude-md/audit.txt", ["audit", "examples/claude-md/before/CLAUDE.md", "--tokens", "estimate"]),
    ("examples/claude-md/compare.md", ["compare", "examples/claude-md/before/CLAUDE.md", "examples/claude-md/after/CLAUDE.md", "--tokens", "estimate", "--md"]),
    ("examples/skill-md/audit.txt", ["audit", "examples/skill-md/before/SKILL.md", "--tokens", "estimate"]),
    ("examples/skill-md/compare.md", ["compare", "examples/skill-md/before/SKILL.md", "examples/skill-md/after/SKILL.md", "--tokens", "estimate", "--md"]),
    ("examples/report.txt", ["report", "examples/claude-md/before/CLAUDE.md", "examples/claude-md/after/CLAUDE.md",
                             "examples/skill-md/before/SKILL.md", "examples/skill-md/after/SKILL.md", "--tokens", "estimate"]),
]


def run(args):
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True, env=env)


class Help(unittest.TestCase):
    def test_help_exits_zero(self):
        for args in (["--help"], ["report", "--help"], ["audit", "--help"], ["compare", "--help"]):
            r = run(args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("usage:", r.stdout)

    def test_no_command_prints_help(self):
        r = run([])
        self.assertEqual(r.returncode, 1)

    def test_missing_file_is_clean_error(self):
        r = run(["report", "does-not-exist.md"])
        self.assertEqual(r.returncode, 1)
        self.assertIn("shrink.py:", r.stderr)


class Examples(unittest.TestCase):
    def test_examples_reproduce(self):
        for expected_rel, args in CASES:
            with self.subTest(expected_rel):
                with open(os.path.join(ROOT, expected_rel), encoding="utf-8") as fh:
                    expected = fh.read()
                r = run(args)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout, expected)

    def test_strict_flags_the_resolved_contradiction(self):
        # The CLAUDE.md example drops one side of a contradiction on purpose; --strict must notice.
        r = run(["compare", "examples/claude-md/before/CLAUDE.md", "examples/claude-md/after/CLAUDE.md", "--tokens", "estimate", "--strict"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("LOST: Always use tabs for indentation.", r.stdout)

    def test_strict_passes_when_nothing_lost(self):
        r = run(["compare", "examples/skill-md/before/SKILL.md", "examples/skill-md/after/SKILL.md", "--tokens", "estimate", "--strict"])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 lost", r.stdout)

    def test_json_outputs_parse(self):
        import json
        for args in (["audit", "examples/skill-md/before/SKILL.md", "--tokens", "estimate", "--json"],
                     ["compare", "examples/skill-md/before/SKILL.md", "examples/skill-md/after/SKILL.md", "--tokens", "estimate", "--json"],
                     ["report", "SKILL.md", "--tokens", "estimate", "--json"]):
            r = run(args)
            self.assertEqual(r.returncode, 0, r.stderr)
            json.loads(r.stdout)

    def test_api_mode_without_key_fails_fast(self):
        r = run(["report", "SKILL.md", "--tokens", "api"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ANTHROPIC_API_KEY", r.stderr)


class OwnSkill(unittest.TestCase):
    def test_own_skill_has_no_duplicates_or_contradictions(self):
        import json
        r = run(["audit", "SKILL.md", "--tokens", "estimate", "--json"])
        a = json.loads(r.stdout)
        self.assertEqual(a["duplicates"], [])
        self.assertEqual(a["contradictions"], [])
        self.assertEqual(a["empty_sections"], [])


if __name__ == "__main__":
    unittest.main()
