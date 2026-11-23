"""Testes do painel da equipe (team_board.py). Somente biblioteca padrão."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dataengineer" / "scripts"
SCRIPT = SCRIPTS / "team_board.py"
sys.path.insert(0, str(SCRIPTS))
import team_board as tb  # noqa: E402


class BoardCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = os.environ.copy()
        self.env["DATAENGINEER_HOME"] = self.tmp.name
        self.env.pop("DATAENGINEER_RUN", None)
        self._old = os.environ.get("DATAENGINEER_HOME")
        os.environ["DATAENGINEER_HOME"] = self.tmp.name

    def tearDown(self):
        if self._old is None:
            os.environ.pop("DATAENGINEER_HOME", None)
        else:
            os.environ["DATAENGINEER_HOME"] = self._old
        self.tmp.cleanup()

    def cli(self, *args, stdin=None, expected=0):
        r = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), *args], env=self.env, input=stdin,
                           capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(r.returncode, expected, msg=f"stdout={r.stdout}\nstderr={r.stderr}")
        return r.stdout.strip()


class MissionFlowTests(BoardCase):
    def test_full_mission(self):
        rid = self.cli("start", "--mode", "construir", "--title", "Pipeline de pedidos", "--project", "/x/lakehouse",
                       "--host", "claude")
        self.assertTrue(rid.startswith("r"))
        self.cli("stage", "contexto")
        self.cli("task", "T1", "--agent", "data-architect", "--status", "running", "--title", "Contratos")
        self.cli("task", "T2", "--agent", "sql_data_modeler", "--status", "queued", "--title", "MERGE silver")
        state = tb.build_state()
        run = state["run"]
        self.assertEqual(run["id"], rid)
        self.assertEqual(run["project"], "lakehouse")  # só o nome da pasta
        self.assertEqual(run["current_stage"], "contexto")
        agents = {a["key"]: a for a in run["agents"]}
        self.assertEqual(agents["data-architect"]["status"], "running")
        self.assertEqual(agents["data-architect"]["task_title"], "Contratos")
        self.assertEqual(agents["sql-data-modeler"]["status"], "queued")
        self.assertEqual(agents["maintainability-reviewer"]["status"], "idle")

        self.cli("stage", "execucao")
        self.assertEqual(tb.build_state()["run"]["stages"][2]["status"], "done")  # etapas anteriores fecham
        self.cli("task", "T1", "--status", "done", "--note", "grain definido")
        self.cli("task", "T2", "--status", "blocked", "--note", "aguardando chave")
        run = tb.build_state()["run"]
        self.assertEqual(run["counts"]["done"], 1)
        self.assertEqual(run["counts"]["blocked"], 1)
        self.cli("finish", "--summary", "Entregue")
        run = tb.build_state()["run"]
        self.assertEqual(run["status"], "done")
        self.assertEqual(run["progress"], 1.0)
        self.assertTrue(all(s["status"] == "done" for s in run["stages"]))

    def test_rejects_unknown_values(self):
        self.cli("start", "--mode", "voar", "--title", "x", expected=2)
        self.cli("start", "--mode", "revisar", "--title", "x")
        self.cli("stage", "dormir", expected=2)
        self.cli("task", "T1", "--agent", "frontend-dev", expected=2)
        self.cli("task", "T1", "--status", "talvez", expected=2)

    def test_command_without_active_mission(self):
        self.cli("stage", "contexto", expected=1)

    def test_secrets_are_not_stored(self):
        self.cli("start", "--mode", "depurar", "--title", "Falha no job")
        self.cli("note", "password=SuperSecreta123 no notebook")
        self.cli("task", "T1", "--agent", "coordinator", "--title", "token ghp_abcdefghijklmnopqrstuvwxyz0123")
        raw = (Path(self.tmp.name) / "board" / "events.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("SuperSecreta123", raw)
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz0123", raw)
        self.assertIn("conteúdo omitido", raw)


class HookTests(BoardCase):
    def hook(self, event, agent, tool_use_id, description="Revisar MERGE", tool="Agent"):
        payload = {"hook_event_name": event, "tool_name": tool, "tool_use_id": tool_use_id, "cwd": "/p/vendas",
                   "session_id": "s1", "tool_input": {"subagent_type": agent, "description": description}}
        return self.cli("hook", stdin=json.dumps(payload))

    def test_hook_links_to_announced_task(self):
        self.cli("start", "--mode", "revisar", "--title", "Revisão")
        self.cli("task", "T1", "--agent", "pipeline-correctness-reviewer", "--status", "queued", "--title", "Corretude")
        self.hook("PreToolUse", "pipeline-correctness-reviewer", "tu_1")
        run = tb.build_state()["run"]
        self.assertEqual(len(run["tasks"]), 1)
        self.assertEqual(run["tasks"][0]["status"], "running")
        self.assertEqual(run["tasks"][0]["title"], "Corretude")
        self.hook("PostToolUse", "pipeline-correctness-reviewer", "tu_1")
        self.assertEqual(tb.build_state()["run"]["tasks"][0]["status"], "done")

    def test_hook_creates_session_when_no_mission(self):
        self.hook("PreToolUse", "data_quality_engineer", "tu_9", "Checar nulos")
        run = tb.build_state()["run"]
        self.assertEqual(run["mode"], "livre")
        self.assertEqual(run["project"], "vendas")
        self.assertEqual(run["tasks"][0]["agent"], "data-quality-engineer")

    def test_hook_ignores_other_agents_and_tools(self):
        self.hook("PreToolUse", "general-purpose", "tu_2")
        self.hook("PreToolUse", "data-architect", "tu_3", tool="Bash")
        self.cli("hook", stdin="isto não é json")
        self.assertFalse((Path(self.tmp.name) / "board" / "events.jsonl").exists())

    def test_hook_decodes_utf8(self):
        self.hook("PreToolUse", "sql-data-modeler", "tu_4", "Modelar dimensão de clientes")
        self.assertEqual(tb.build_state()["run"]["tasks"][0]["title"], "Modelar dimensão de clientes")


class ServerAndExportTests(BoardCase):
    def test_http_api_and_cors(self):
        self.cli("start", "--mode", "construir", "--title", "API")
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), tb.BoardHandler)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health") as r:
                self.assertEqual(json.load(r)["app"], tb.APP)
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state") as r:
                self.assertEqual(json.load(r)["run"]["title"], "API")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
                html = r.read().decode("utf-8")
                self.assertIn('"mode": "live"', html)
                self.assertNotIn("/*__MDE_CONFIG__*/", html)
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/state", headers={"Origin": "https://exemplo.com"})
            with urllib.request.urlopen(req) as r:
                self.assertIsNone(r.headers.get("Access-Control-Allow-Origin"))
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/state", headers={"Origin": "null"})
            with urllib.request.urlopen(req) as r:
                self.assertEqual(r.headers.get("Access-Control-Allow-Origin"), "null")
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_export_has_demo_and_snapshot(self):
        dest = Path(self.tmp.name) / "painel.html"
        self.cli("export", str(dest))
        html = dest.read_text(encoding="utf-8")
        self.assertIn('"mode": "file"', html)
        self.assertIn("Pipeline incremental de pedidos", html)  # quadros da demonstração

    def test_demo_frames_progress(self):
        frames = tb.demo_frames(8)
        self.assertEqual(len(frames), 8)
        self.assertLess(frames[0]["run"]["progress"], frames[-1]["run"]["progress"])
        self.assertEqual(frames[-1]["run"]["status"], "done")


if __name__ == "__main__":
    unittest.main()
