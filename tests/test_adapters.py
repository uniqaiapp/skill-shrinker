"""Structure checks shared by every uniqaiapp repo: one source of truth (SKILL.md), adapters point
at it, versions match, and no tracked text file contains a forbidden string."""
import json
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "skill-shrinker"

# Built from pieces so this file does not trip its own check.
FORBIDDEN = [
    "aeo" + "ria", "rich" + "peach", "/Use" + "rs/", "/Volu" + "mes/", "node_" + "modules",
    "sk-" + "ant-", "sk_" + "live", "api_" + "key=", "API_" + "KEY=<" + "real", "TODO: " + "fill", "lorem " + "ipsum",
]
TEXT_EXT = {".md", ".py", ".json", ".yml", ".yaml", ".mdc", ".txt", ".svg", ".cff", ".editorconfig", ".gitignore", ".gitattributes", ""}


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        files = [f for f in out.split("\n") if f]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    files = []
    for d, dirs, names in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in (".git", "__pycache__")]
        for n in names:
            files.append(os.path.relpath(os.path.join(d, n), ROOT))
    return files


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def frontmatter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md has no YAML frontmatter"
    fm = {}
    for line in m.group(1).split("\n"):
        if line.startswith("  ") and ":" in line:  # nested under metadata:
            k, v = line.strip().split(":", 1)
            fm["metadata." + k.strip()] = v.strip()
        elif ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


class SkillFrontmatter(unittest.TestCase):
    def setUp(self):
        self.fm = frontmatter(read("SKILL.md"))

    def test_name_equals_repo(self):
        self.assertEqual(self.fm["name"], REPO)
        self.assertRegex(self.fm["name"], r"^[a-z0-9-]{1,64}$")

    def test_description_single_line_and_length(self):
        d = self.fm["description"]
        self.assertTrue(1 <= len(d) <= 1024, len(d))
        self.assertNotIn("\n", d)
        for phrase in ("CLAUDE.md", "AGENTS.md", "SKILL.md", "Not for"):
            self.assertIn(phrase, d)

    def test_body_under_500_lines(self):
        self.assertLess(read("SKILL.md").count("\n"), 500)

    def test_versions_match(self):
        plugin = json.loads(read(".claude-plugin/plugin.json"))
        self.assertEqual(plugin["name"], REPO)
        self.assertEqual(plugin["version"], self.fm["metadata.version"])
        self.assertEqual(plugin["skills"], ["./"])
        top = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(top, self.fm["metadata.version"])


class Adapters(unittest.TestCase):
    def test_cursor_rule(self):
        t = read(".cursor/rules/%s.mdc" % REPO)
        self.assertIn("@SKILL.md", t)
        self.assertIn("alwaysApply: false", t)

    def test_agents_and_codex_point_to_skill(self):
        self.assertIn("SKILL.md", read("AGENTS.md"))
        self.assertIn("SKILL.md", read("codex/INSTRUCTIONS.md"))

    def test_required_files(self):
        for rel in ("README.md", "LICENSE", "CONTRIBUTING.md", "CHANGELOG.md", ".github/workflows/ci.yml",
                    ".github/ISSUE_TEMPLATE/bug_report.md", ".github/ISSUE_TEMPLATE/feature_request.md",
                    ".github/ISSUE_TEMPLATE/config.yml", ".github/PULL_REQUEST_TEMPLATE.md", ".github/repo.json",
                    "assets/banner.svg", "assets/banner-light.svg", "assets/demo.svg", "assets/social-preview.png",
                    "assets/icon.svg", "examples/README.md", "tests/run.py"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_repo_json(self):
        meta = json.loads(read(".github/repo.json"))
        self.assertEqual(meta["name"], REPO)
        self.assertIn("utm_campaign=" + REPO, meta["homepage"])
        self.assertLessEqual(len(meta["topics"]), 20)


class Hygiene(unittest.TestCase):
    def test_no_forbidden_strings(self):
        hits = []
        for rel in tracked_files():
            ext = os.path.splitext(rel)[1].lower()
            base = os.path.basename(rel)
            if ext not in TEXT_EXT and base not in (".gitignore", ".gitattributes", ".editorconfig", "LICENSE"):
                continue
            try:
                text = read(rel)
            except (UnicodeDecodeError, OSError):
                continue
            low = text.lower()
            for bad in FORBIDDEN:
                if bad.lower() in low:
                    hits.append("%s: %s" % (rel, bad))
        self.assertEqual(hits, [])

    def test_copyright_is_brand(self):
        for rel in tracked_files():
            if not rel.endswith((".md", ".py", "LICENSE")):
                continue
            for line in read(rel).split("\n"):
                if ("Copyright " + "(c)") in line:
                    self.assertIn("UniqAI", line, "%s: %s" % (rel, line))

    def test_readme_links(self):
        t = read("README.md")
        self.assertEqual(t.count("<sub>Made by"), 1, "exactly one footer")
        self.assertLessEqual(t.count("uniqai.app/"), 3)
        for m in re.finditer(r"https://uniqai\.app/[^\s)\"']*", t):
            self.assertIn("utm_campaign=" + REPO, m.group(0))
        self.assertTrue(os.path.exists(os.path.join(ROOT, "assets/banner.svg")))

    def test_assets_size(self):
        for rel, limit in (("assets/banner.svg", 15 * 1024), ("assets/banner-light.svg", 15 * 1024),
                           ("assets/demo.svg", 60 * 1024), ("assets/social-preview.png", 120 * 1024)):
            self.assertLessEqual(os.path.getsize(os.path.join(ROOT, rel)), limit, rel)


if __name__ == "__main__":
    unittest.main()
