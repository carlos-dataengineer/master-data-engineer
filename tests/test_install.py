"""Testa o instalador numa pasta pessoal falsa (nada toca o seu Claude Code ou Codex reais)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if k not in ("CODEX_HOME", "DATAENGINEER_HOME")}
        self.env.update({"HOME": str(self.home), "USERPROFILE": str(self.home), "MDE_NO_OPEN": "1",
                         "MDE_NO_SERVER": "1", "NO_COLOR": "1"})

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, *args, expected=0):
        r = subprocess.run([sys.executable, "-X", "utf8", str(INSTALLER), *args], env=self.env, capture_output=True,
                           text=True, encoding="utf-8", check=False)
        self.assertEqual(r.returncode, expected, msg=f"stdout={r.stdout}\nstderr={r.stderr}")
        return r.stdout

    def settings(self):
        return json.loads((self.home / ".claude" / "settings.json").read_text(encoding="utf-8"))

    def test_install_reinstall_uninstall(self):
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "settings.json").write_text(json.dumps({"model": "x", "hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo meu-hook"}]}]}}), encoding="utf-8")
        self.install()
        for rel in (".claude/skills/dataengineer/SKILL.md", ".claude/skills/dataengineer/scripts/team_board.py",
                    ".agents/skills/dataengineer/SKILL.md", ".agents/skills/dataengineer/agents/openai.yaml",
                    ".claude/agents/data-architect.md", ".codex/agents/data_architect.toml",
                    "MasterDataEngineer/painel.html", "MasterDataEngineer/app/scripts/team_board.py",
                    "MasterDataEngineer/Abrir painel.cmd", "MasterDataEngineer/abrir-painel.sh"):
            self.assertTrue((self.home / rel).exists(), rel)
        self.assertEqual(len(list((self.home / ".claude" / "agents").glob("*.md"))), 8)
        self.assertEqual(len(list((self.home / ".codex" / "agents").glob("*.toml"))), 8)
        s = self.settings()
        self.assertEqual(s["model"], "x")
        self.assertEqual(len(s["hooks"]["PreToolUse"]), 2)
        self.assertIn("echo meu-hook", json.dumps(s))
        self.assertTrue((self.home / ".claude" / "settings.json.bak-mde").exists())

        self.install()  # reinstalar não duplica hooks
        self.assertEqual(len(self.settings()["hooks"]["PreToolUse"]), 2)
        self.assertEqual(len(self.settings()["hooks"]["PostToolUse"]), 1)

        self.install("--uninstall")
        self.assertFalse((self.home / ".claude" / "skills" / "dataengineer").exists())
        self.assertFalse((self.home / ".agents" / "skills" / "dataengineer").exists())
        self.assertEqual(list((self.home / ".claude" / "agents").glob("*.md")), [])
        s = self.settings()
        self.assertEqual(s["hooks"], {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo meu-hook"}]}]})
        self.assertFalse((self.home / "MasterDataEngineer" / "app").exists())

    def test_preserves_foreign_skill_and_agent(self):
        foreign = self.home / ".claude" / "skills" / "dataengineer"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("---\nname: dataengineer\ndescription: outra coisa\n---\n", encoding="utf-8")
        agent = self.home / ".claude" / "agents" / "data-architect.md"
        agent.parent.mkdir(parents=True)
        agent.write_text("meu agente", encoding="utf-8")
        out = self.install("--skip-codex", "--no-hooks")
        self.assertIn("Pulei", out)
        self.assertIn("outra coisa", (foreign / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(agent.read_text(encoding="utf-8"), "meu agente")
        self.assertFalse((self.home / ".claude" / "settings.json").exists())
        self.install("--skip-codex", "--no-hooks", "--force")
        self.assertIn("Engenharia de Dados", (foreign / "SKILL.md").read_text(encoding="utf-8"))

    def test_project_scope(self):
        proj = self.home / "meu-projeto"
        proj.mkdir()
        self.install("--scope", "project", "--project", str(proj))
        self.assertTrue((proj / ".claude" / "skills" / "dataengineer" / "SKILL.md").exists())
        self.assertTrue((proj / ".agents" / "skills" / "dataengineer" / "SKILL.md").exists())
        self.assertTrue((proj / ".codex" / "agents" / "sql_data_modeler.toml").exists())
        self.assertTrue((proj / ".claude" / "settings.local.json").exists())
        self.assertFalse((self.home / ".claude" / "skills").exists())

    def test_invalid_settings_are_left_alone(self):
        (self.home / ".claude").mkdir()
        bad = self.home / ".claude" / "settings.json"
        bad.write_text("{ isto não é json", encoding="utf-8")
        out = self.install("--skip-codex")
        self.assertIn("não é um JSON válido", out)
        self.assertEqual(bad.read_text(encoding="utf-8"), "{ isto não é json")


if __name__ == "__main__":
    unittest.main()
