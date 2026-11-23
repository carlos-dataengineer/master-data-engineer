#!/usr/bin/env python3
"""Painel da equipe Master Data Engineer: registro de eventos e servidor local em tempo real.

O coordenador (skill dataengineer) registra a missão, as etapas e as tarefas de cada agente.
No Claude Code, hooks opcionais registram sozinhos o início e o fim de cada subagente.
O painel (assets/painel.html) mostra tudo ao vivo em http://127.0.0.1:47821.

Somente biblioteca padrão. O servidor escuta apenas em 127.0.0.1, é somente leitura e não
faz chamadas de rede. Eventos ficam em ~/MasterDataEngineer/board/events.jsonl.

Uso rápido:
    python team_board.py ensure --open            # sobe o painel (se preciso) e abre no navegador
    python team_board.py start --mode construir --title "Pipeline de pedidos" --host claude
    python team_board.py stage contexto
    python team_board.py task T1 --agent data-architect --status running --title "Desenhar contratos"
    python team_board.py task T1 --status done
    python team_board.py finish --summary "Pipeline entregue com testes"
    python team_board.py demo --live              # missão simulada, para conhecer o painel
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

APP = "master-data-engineer"
SCHEMA = 1
DEFAULT_PORT = 47821
HERE = Path(__file__).resolve().parent
PANEL_FILE = HERE.parent / "assets" / "painel.html"
MAX_TEXT = 240
MAX_EVENTS_BYTES = 5_000_000

AGENTS: list[dict[str, str]] = [
    {"key": "coordinator", "name": "Coordenador", "role": "Skill dataengineer: conduz, delega e consolida", "short": "CO", "color": "#7c8cff"},
    {"key": "data-architect", "name": "Data Architect", "role": "Requisitos, contratos, grain e arquitetura", "short": "DA", "color": "#38bdf8"},
    {"key": "databricks-pyspark-engineer", "name": "Databricks / PySpark", "role": "Python, PySpark, notebooks e Jobs", "short": "PS", "color": "#f97316"},
    {"key": "sql-data-modeler", "name": "SQL Data Modeler", "role": "SQL, joins, chaves e modelagem", "short": "SQ", "color": "#a78bfa"},
    {"key": "data-quality-engineer", "name": "Data Quality", "role": "Regras, integridade, reconciliação e testes", "short": "DQ", "color": "#22c55e"},
    {"key": "performance-cost-engineer", "name": "Performance & Cost", "role": "Shuffle, skew, partições e custo", "short": "PC", "color": "#eab308"},
    {"key": "governance-security-reviewer", "name": "Governance & Security", "role": "Unity Catalog, permissões e segredos", "short": "GS", "color": "#ef4444"},
    {"key": "pipeline-correctness-reviewer", "name": "Pipeline Correctness", "role": "Revisão independente de corretude", "short": "CR", "color": "#14b8a6"},
    {"key": "maintainability-reviewer", "name": "Maintainability", "role": "Simplicidade, legibilidade e manutenção", "short": "MT", "color": "#ec4899"},
]
AGENT_KEYS = {a["key"] for a in AGENTS}

STAGES: list[tuple[str, str]] = [
    ("modo", "Modo de trabalho"),
    ("contexto", "Contexto e requisitos"),
    ("memoria", "Memória contextual"),
    ("selecao", "Seleção de especialistas"),
    ("execucao", "Execução"),
    ("validacao", "Testes e revisão"),
    ("consolidacao", "Consolidação"),
    ("entrega", "Entrega"),
]
STAGE_KEYS = [k for k, _ in STAGES]
STAGE_ALIASES = {
    "mode": "modo", "context": "contexto", "requisitos": "contexto", "memory": "memoria", "memória": "memoria",
    "selection": "selecao", "seleção": "selecao", "execution": "execucao", "execução": "execucao",
    "implementacao": "execucao", "implementação": "execucao", "testes": "validacao", "revisao": "validacao",
    "revisão": "validacao", "validação": "validacao", "review": "validacao", "consolidação": "consolidacao",
    "delivery": "entrega",
}
MODES = {"construir": "Construção", "revisar": "Revisão", "depurar": "Debugging", "livre": "Sessão livre"}
MODE_ALIASES = {"build": "construir", "construcao": "construir", "construção": "construir", "1": "construir",
                "review": "revisar", "revisao": "revisar", "revisão": "revisar", "2": "revisar",
                "debug": "depurar", "debugging": "depurar", "corrigir": "depurar", "3": "depurar"}
TASK_STATUSES = ("queued", "running", "review", "done", "blocked", "failed")
STATUS_ALIASES = {"fila": "queued", "pendente": "queued", "executando": "running", "em-execucao": "running",
                  "revisao": "review", "revisão": "review", "concluida": "done", "concluída": "done", "ok": "done",
                  "bloqueada": "blocked", "falhou": "failed", "erro": "failed"}

SENSITIVE = [
    re.compile(r"(?i)\b(api[_-]?key|client[_-]?secret|password|passwd|senha|secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*\S{6,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bdapi[0-9a-f]{32}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
]

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


# ---------------------------------------------------------------- utilidades

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def app_home() -> Path:
    raw = os.environ.get("DATAENGINEER_HOME")
    return Path(raw).expanduser() if raw else Path.home() / "MasterDataEngineer"


def board_dir() -> Path:
    raw = os.environ.get("DATAENGINEER_BOARD_HOME")
    path = Path(raw).expanduser() if raw else app_home() / "board"
    path.mkdir(parents=True, exist_ok=True)
    return path


def events_file() -> Path:
    return board_dir() / "events.jsonl"


def server_file() -> Path:
    return board_dir() / "server.json"


def clean(text: Any, limit: int = MAX_TEXT) -> str:
    """Texto curto e de uma linha; troca o que parece credencial por um aviso."""
    if text is None:
        return ""
    value = " ".join(str(text).split())
    for pat in SENSITIVE:
        if pat.search(value):
            return "[conteúdo omitido: parece conter uma credencial]"
    return value if len(value) <= limit else value[: limit - 1] + "…"


def norm_agent(raw: str | None) -> str:
    if not raw:
        return "coordinator"
    key = raw.strip().lower().replace("_", "-").replace(" ", "-")
    key = key.split(":")[-1]  # plugin:agente
    if key in ("coordenador", "dataengineer", "coord"):
        return "coordinator"
    return key


def norm_stage(raw: str) -> str:
    key = raw.strip().lower()
    key = STAGE_ALIASES.get(key, key)
    if key not in STAGE_KEYS:
        raise ValueError(f"Etapa desconhecida: {raw}. Use: {', '.join(STAGE_KEYS)}")
    return key


def norm_mode(raw: str) -> str:
    key = raw.strip().lower()
    key = MODE_ALIASES.get(key, key)
    if key not in MODES:
        raise ValueError(f"Modo desconhecido: {raw}. Use: construir, revisar ou depurar")
    return key


def norm_status(raw: str) -> str:
    key = raw.strip().lower()
    key = STATUS_ALIASES.get(key, key)
    if key not in TASK_STATUSES:
        raise ValueError(f"Status desconhecido: {raw}. Use: {', '.join(TASK_STATUSES)}")
    return key


# ---------------------------------------------------------------- eventos

_lock = threading.Lock()


def append(event: dict[str, Any], ts: datetime | None = None) -> dict[str, Any]:
    event = {"v": SCHEMA, "ts": iso(ts or utc_now()), **event}
    line = json.dumps(event, ensure_ascii=False)
    path = events_file()
    with _lock, open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return event


def read_events(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or events_file()
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(ev, dict) and ev.get("type"):
                out.append(ev)
    return out


def new_run_id(now: datetime) -> str:
    return now.strftime("r%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]


def active_run_id(events: Iterable[dict[str, Any]]) -> str | None:
    started: dict[str, str] = {}
    ended: set[str] = set()
    for ev in events:
        if ev["type"] == "run.start":
            started[ev["run"]] = ev["ts"]
        elif ev["type"] == "run.end":
            ended.add(ev.get("run", ""))
    live = [(ts, rid) for rid, ts in started.items() if rid not in ended]
    return max(live)[1] if live else None


def resolve_run(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("DATAENGINEER_RUN")
    if env:
        return env
    rid = active_run_id(read_events())
    if not rid:
        raise SystemExit("Nenhuma missão ativa. Comece com: team_board.py start --mode construir --title \"...\"")
    return rid


# ---------------------------------------------------------------- estado

def _blank_run(ev: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": ev["run"], "title": ev.get("title") or "Missão sem título", "mode": ev.get("mode", "livre"),
        "mode_label": MODES.get(ev.get("mode", "livre"), "Sessão livre"), "project": ev.get("project") or "",
        "host": ev.get("host") or "", "status": "active", "started": ev["ts"], "ended": None, "summary": "",
        "current_stage": None,
        "stages": {k: {"key": k, "label": label, "status": "pending", "started": None, "ended": None, "note": ""}
                   for k, label in STAGES},
        "tasks": {}, "task_order": [], "feed": [], "updated": ev["ts"],
    }


def _feed(run: dict[str, Any], ev: dict[str, Any], kind: str, text: str, agent: str = "coordinator",
          status: str = "") -> None:
    run["feed"].append({"ts": ev["ts"], "kind": kind, "agent": agent, "text": text, "status": status})


def _set_stage(run: dict[str, Any], key: str, ts: str, status: str = "running", note: str = "") -> None:
    idx = STAGE_KEYS.index(key)
    for k in STAGE_KEYS[:idx]:
        st = run["stages"][k]
        if st["status"] != "done":
            st["status"] = "done"
            st["started"] = st["started"] or ts
            st["ended"] = st["ended"] or ts
    st = run["stages"][key]
    if status == "done":
        st["status"] = "done"
        st["started"] = st["started"] or ts
        st["ended"] = ts
    else:
        st["status"] = "running"
        st["started"] = st["started"] or ts
        st["ended"] = None
        run["current_stage"] = key
        for k in STAGE_KEYS[idx + 1:]:  # voltou uma etapa (ex.: revisão reabriu execução)
            if run["stages"][k]["status"] == "running":
                run["stages"][k]["status"] = "pending"
    if note:
        st["note"] = note


def _apply_task(run: dict[str, Any], ev: dict[str, Any]) -> None:
    ts = ev["ts"]
    tasks = run["tasks"]
    agent = norm_agent(ev.get("agent")) if ev.get("agent") else None
    status = ev.get("status", "running")
    tid = ev.get("task")
    hook_id = ev.get("hook_id")

    if ev.get("source") == "hook" and hook_id:
        linked = next((t for t in tasks.values() if t.get("hook_id") == hook_id), None)
        if linked is None and status == "running":
            # liga ao item que o coordenador já anunciou para esse agente
            linked = next((tasks[i] for i in reversed(run["task_order"])
                           if tasks[i]["agent"] == agent and tasks[i]["status"] in ("queued", "running")
                           and not tasks[i].get("hook_id")), None)
        if linked is not None:
            tid = linked["id"]
            linked["hook_id"] = hook_id
        elif not tid:
            tid = "H" + hook_id[-6:]

    if not tid:
        return
    task = tasks.get(tid)
    if task is None:
        task = {"id": tid, "agent": agent or "coordinator", "title": ev.get("title") or tid, "status": "queued",
                "note": "", "created": ts, "started": None, "ended": None, "updated": ts,
                "source": ev.get("source", "coordinator")}
        if hook_id:
            task["hook_id"] = hook_id
        tasks[tid] = task
        run["task_order"].append(tid)
    if agent:
        task["agent"] = agent
    if ev.get("title") and (ev.get("source") != "hook" or task["title"] == tid):
        task["title"] = ev["title"]
    if ev.get("note"):
        task["note"] = ev["note"]
    previous = task["status"]
    task["status"] = status
    task["updated"] = ts
    if status == "running" and not task["started"]:
        task["started"] = ts
    if status in ("done", "failed"):
        task["started"] = task["started"] or ts
        task["ended"] = ts
    elif status in ("queued", "running", "review"):
        task["ended"] = None
    if previous != status or ev.get("note"):
        verb = {"queued": "entrou na fila", "running": "começou", "review": "foi para revisão",
                "done": "concluiu", "blocked": "está bloqueada", "failed": "falhou"}[status]
        text = f"{task['title']} — {verb}"
        if ev.get("note"):
            text += f" · {ev['note']}"
        _feed(run, ev, "task", text, task["agent"], status)
    if status == "running" and run["current_stage"] in (None, "modo", "contexto", "memoria", "selecao") \
            and run["mode"] != "livre" and ev.get("source") == "hook":
        _set_stage(run, "execucao", ts)


def fold(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    for ev in events:
        typ = ev.get("type")
        rid = ev.get("run")
        if typ == "run.start":
            run = runs[rid] = _blank_run(ev)
            _set_stage(run, "modo", ev["ts"], "done")
            _feed(run, ev, "run", f"Missão iniciada: {run['title']} ({run['mode_label']})")
            continue
        run = runs.get(rid)
        if run is None:
            continue
        run["updated"] = ev["ts"]
        if typ == "stage":
            _set_stage(run, ev["stage"], ev["ts"], ev.get("status", "running"), ev.get("note", ""))
            label = dict(STAGES)[ev["stage"]]
            verb = "concluída" if ev.get("status") == "done" else "em andamento"
            text = f"Etapa {label} {verb}" + (f" · {ev['note']}" if ev.get("note") else "")
            _feed(run, ev, "stage", text)
        elif typ == "task":
            _apply_task(run, ev)
        elif typ == "note":
            _feed(run, ev, "note", ev.get("text", ""), norm_agent(ev.get("agent")))
        elif typ == "run.end":
            run["status"] = ev.get("status", "done")
            run["ended"] = ev["ts"]
            run["summary"] = ev.get("summary", "")
            if run["status"] == "done":
                for st in run["stages"].values():
                    if st["status"] != "done":
                        st["status"] = "done"
                        st["started"] = st["started"] or ev["ts"]
                        st["ended"] = st["ended"] or ev["ts"]
                run["current_stage"] = None
            else:
                cur = run["current_stage"]
                if cur:
                    run["stages"][cur]["status"] = "failed" if run["status"] == "failed" else "pending"
            label = {"done": "concluída", "failed": "encerrada com falha", "cancelled": "cancelada"}.get(run["status"], run["status"])
            _feed(run, ev, "run", f"Missão {label}" + (f": {run['summary']}" if run["summary"] else ""), "coordinator",
                  "done" if run["status"] == "done" else "failed")
    return runs


def _agent_view(run: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = [run["tasks"][i] for i in run["task_order"]]
    out = []
    priority = {"running": 0, "review": 1, "blocked": 2, "failed": 3, "queued": 4, "done": 5}
    for meta in AGENTS:
        mine = [t for t in tasks if t["agent"] == meta["key"]]
        current = [t for t in mine if t["status"] != "done"]
        cur = None
        if current:
            best = min(priority[t["status"]] for t in current)
            cur = max((t for t in current if priority[t["status"]] == best), key=lambda t: t["updated"])
        done = [t for t in mine if t["status"] == "done"]
        if cur:
            status = cur["status"]
        elif done:
            status = "done"
        else:
            status = "idle"
        if meta["key"] == "coordinator" and not cur:
            if run["status"] == "active":
                status = "running"
            elif run["status"] == "done":
                status = "done"
            stage = run["current_stage"]
            label = dict(STAGES).get(stage or "", "")
            out.append({**meta, "status": status, "task_id": None,
                        "task_title": f"Conduzindo: {label}" if (run["status"] == "active" and label) else
                        (run["summary"] or "Missão encerrada" if run["status"] != "active" else "Aguardando"),
                        "since": run["stages"][stage]["started"] if stage else run["started"],
                        "done": len(done), "total": len(mine)})
            continue
        out.append({**meta, "status": status, "task_id": cur["id"] if cur else None,
                    "task_title": cur["title"] if cur else (done[-1]["title"] if done else ""),
                    "since": (cur["started"] or cur["updated"]) if cur else (done[-1]["ended"] if done else None),
                    "done": len(done), "total": len(mine)})
    return out


def public_run(run: dict[str, Any], feed_limit: int = 120) -> dict[str, Any]:
    tasks = [run["tasks"][i] for i in run["task_order"]]
    counts = {s: sum(1 for t in tasks if t["status"] == s) for s in TASK_STATUSES}
    stages = [run["stages"][k] for k in STAGE_KEYS]
    done_stages = sum(1 for s in stages if s["status"] == "done")
    running = 0.5 if any(s["status"] == "running" for s in stages) else 0
    progress = 1.0 if run["status"] == "done" else round((done_stages + running) / len(stages), 3)
    return {
        **{k: run[k] for k in ("id", "title", "mode", "mode_label", "project", "host", "status", "started", "ended",
                               "summary", "current_stage", "updated")},
        "stages": stages,
        "tasks": [{k: v for k, v in t.items() if k != "hook_id"} for t in tasks],
        "agents": _agent_view(run),
        "feed": run["feed"][-feed_limit:][::-1],
        "counts": counts,
        "progress": progress,
    }


def summary_run(run: dict[str, Any]) -> dict[str, Any]:
    pub = public_run(run, feed_limit=0)
    return {k: pub[k] for k in ("id", "title", "mode", "mode_label", "project", "host", "status", "started", "ended",
                                "counts", "progress", "updated", "summary")}


def build_state(events: list[dict[str, Any]] | None = None, run_id: str | None = None,
                now: datetime | None = None) -> dict[str, Any]:
    events = read_events() if events is None else events
    runs = fold(events)
    ordered = sorted(runs.values(), key=lambda r: r["started"], reverse=True)
    selected = None
    if run_id and run_id in runs:
        selected = runs[run_id]
    elif ordered:
        active = [r for r in ordered if r["status"] == "active"]
        selected = max(active, key=lambda r: r["updated"]) if active else ordered[0]
    return {
        "app": APP, "schema": SCHEMA, "now": iso(now or utc_now()),
        "agents_meta": AGENTS, "stages_meta": [{"key": k, "label": label} for k, label in STAGES],
        "modes": MODES,
        "runs": [summary_run(r) for r in ordered[:60]],
        "run": public_run(selected) if selected else None,
    }


# ---------------------------------------------------------------- hooks do Claude Code

def handle_hook(raw: str) -> None:
    """Recebe o JSON de PreToolUse/PostToolUse (ferramenta Task/Agent). Nunca falha."""
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return
    if data.get("tool_name") not in ("Task", "Agent"):
        return
    tool_input = data.get("tool_input") or {}
    agent = norm_agent(tool_input.get("subagent_type"))
    if agent not in AGENT_KEYS or agent == "coordinator":
        return
    event_name = data.get("hook_event_name", "")
    if event_name not in ("PreToolUse", "PostToolUse"):
        return
    desc = clean(tool_input.get("description") or "Tarefa delegada", 160)
    hook_id = data.get("tool_use_id") or hashlib.sha256(
        f"{data.get('session_id')}|{agent}|{desc}".encode("utf-8")).hexdigest()[:16]
    events = read_events()
    rid = active_run_id(events)
    if not rid:
        if event_name != "PreToolUse":
            return
        now = utc_now()
        rid = new_run_id(now)
        cwd = data.get("cwd") or ""
        append({"type": "run.start", "run": rid, "mode": "livre", "title": "Sessão sem missão declarada",
                "project": clean(Path(cwd).name if cwd else "", 80), "host": "claude"}, now)
    status = "running" if event_name == "PreToolUse" else "done"
    response = data.get("tool_response")
    if status == "done" and isinstance(response, dict) and response.get("is_error"):
        status = "failed"
    append({"type": "task", "run": rid, "agent": agent, "status": status, "title": desc,
            "source": "hook", "hook_id": hook_id})


# ---------------------------------------------------------------- servidor

class BoardHandler(BaseHTTPRequestHandler):
    server_version = "MasterDataEngineerBoard/1"

    def log_message(self, fmt: str, *args: Any) -> None:  # silencioso
        return

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionError, TimeoutError):  # navegador fechou a aba no meio da conversa
            pass

    def _cors(self) -> None:
        # Só o próprio painel (mesma origem) ou o arquivo local (origem "null") podem ler a API.
        if self.headers.get("Origin") == "null":
            self.send_header("Access-Control-Allow-Origin", "null")

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any, code: int = 200) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        run = (qs.get("run") or [None])[0]
        if url.path in ("/", "/index.html", "/painel"):
            html = render_panel({"mode": "live"})
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        elif url.path == "/api/health":
            self._json({"app": APP, "ok": True, "pid": os.getpid()})
        elif url.path == "/api/state":
            self._json(build_state(run_id=run))
        elif url.path == "/api/demo":
            self._json(demo_frames())
        elif url.path == "/api/stream":
            self._stream(run)
        else:
            self._json({"error": "não encontrado"}, 404)

    def _stream(self, run: str | None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()
        last_sig = None
        last_sent = 0.0
        path = events_file()
        try:
            while True:
                try:
                    st = path.stat()
                    sig = (st.st_mtime_ns, st.st_size)
                except FileNotFoundError:
                    sig = None
                now = time.monotonic()
                if sig != last_sig or now - last_sent > 10:
                    payload = json.dumps(build_state(run_id=run), ensure_ascii=False)
                    self.wfile.write(f"event: state\ndata: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    last_sig, last_sent = sig, now
                time.sleep(0.4)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            return


def render_panel(config: dict[str, Any]) -> str:
    html = PANEL_FILE.read_text(encoding="utf-8")
    blob = json.dumps(config, ensure_ascii=False).replace("</", "<\\/")
    return html.replace("/*__MDE_CONFIG__*/null", blob, 1)


def health(port: int, timeout: float = 0.8) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get("app") == APP
    except Exception:  # noqa: BLE001
        return False


def known_port() -> int:
    env = os.environ.get("DATAENGINEER_BOARD_PORT")
    if env and env.isdigit():
        return int(env)
    try:
        return int(json.loads(server_file().read_text(encoding="utf-8")).get("port", DEFAULT_PORT))
    except Exception:  # noqa: BLE001
        return DEFAULT_PORT


def serve(port: int, open_browser: bool) -> int:
    httpd = None
    for candidate in range(port, port + 10):
        if health(candidate, 0.3):
            print(f"Painel já está no ar: http://127.0.0.1:{candidate}")
            if open_browser:
                webbrowser.open(f"http://127.0.0.1:{candidate}")
            return 0
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", candidate), BoardHandler)
            port = candidate
            break
        except OSError:
            continue
    if httpd is None:
        print("Não encontrei uma porta livre para o painel.", file=sys.stderr)
        return 1
    httpd.daemon_threads = True
    server_file().write_text(json.dumps({"port": port, "pid": os.getpid(), "started": iso(utc_now())}),
                             encoding="utf-8")
    url = f"http://127.0.0.1:{port}"
    print(f"Painel da equipe no ar: {url}  (Ctrl+C para parar)", flush=True)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def ensure(open_browser: bool, port: int | None = None) -> int:
    port = port or known_port()
    if health(port):
        url = f"http://127.0.0.1:{port}"
    else:
        log = open(board_dir() / "server.log", "a", encoding="utf-8")
        cmd = [sys.executable, str(Path(__file__).resolve()), "serve", "--port", str(port)]
        kwargs: dict[str, Any] = {"stdout": log, "stderr": log, "stdin": subprocess.DEVNULL, "close_fds": True}
        if os.name == "nt":
            pyw = Path(sys.executable).with_name("pythonw.exe")
            if pyw.exists():
                cmd[0] = str(pyw)
            kwargs["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(cmd, **kwargs)  # noqa: S603
        deadline = time.time() + 8
        url = None
        while time.time() < deadline:
            time.sleep(0.25)
            p = known_port()
            if health(p, 0.4):
                url = f"http://127.0.0.1:{p}"
                break
        if not url:
            print("O painel não respondeu. Veja " + str(board_dir() / "server.log"), file=sys.stderr)
            return 1
    print(f"Painel da equipe: {url}")
    if open_browser:
        webbrowser.open(url)
    return 0


def stop() -> int:
    try:
        info = json.loads(server_file().read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        print("Painel não está registrado como em execução.")
        return 0
    port, pid = info.get("port", DEFAULT_PORT), info.get("pid")
    if pid and health(port):
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError as exc:
            print(f"Não consegui parar o processo {pid}: {exc}", file=sys.stderr)
            return 1
    server_file().unlink(missing_ok=True)
    print("Painel parado.")
    return 0


# ---------------------------------------------------------------- demonstração

DEMO_SCRIPT: list[tuple[int, dict[str, Any]]] = [
    (0, {"type": "run.start", "mode": "construir", "title": "Pipeline incremental de pedidos (bronze → silver → gold)",
         "project": "lakehouse-vendas", "host": "claude"}),
    (8, {"type": "stage", "stage": "contexto"}),
    (10, {"type": "task", "task": "T1", "agent": "data-architect", "status": "running",
          "title": "Levantar fontes, grain e contrato de pedidos"}),
    (40, {"type": "task", "task": "T1", "status": "done", "note": "grain = 1 linha por item de pedido"}),
    (44, {"type": "stage", "stage": "memoria", "note": "3 memórias do projeto recuperadas"}),
    (50, {"type": "stage", "stage": "selecao", "note": "5 especialistas convocados"}),
    (54, {"type": "task", "task": "T2", "agent": "databricks-pyspark-engineer", "status": "queued",
          "title": "Ingestão incremental com Auto Loader (bronze)"}),
    (54, {"type": "task", "task": "T3", "agent": "sql-data-modeler", "status": "queued",
          "title": "MERGE da silver com deduplicação por chave"}),
    (55, {"type": "task", "task": "T4", "agent": "data-quality-engineer", "status": "queued",
          "title": "Expectativas de schema, nulos e unicidade"}),
    (56, {"type": "task", "task": "T5", "agent": "governance-security-reviewer", "status": "queued",
          "title": "Permissões no Unity Catalog e uso de secrets"}),
    (58, {"type": "stage", "stage": "execucao"}),
    (60, {"type": "task", "task": "T2", "status": "running"}),
    (62, {"type": "task", "task": "T3", "status": "running"}),
    (64, {"type": "task", "task": "T5", "status": "running"}),
    (95, {"type": "task", "task": "T5", "status": "done", "note": "segredo lido via dbutils.secrets; grants mínimos"}),
    (110, {"type": "task", "task": "T2", "status": "review", "note": "checkpoint e schema evolution configurados"}),
    (112, {"type": "task", "task": "T4", "status": "running"}),
    (125, {"type": "task", "task": "T6", "agent": "performance-cost-engineer", "status": "running",
           "title": "Avaliar skew no join com clientes"}),
    (140, {"type": "task", "task": "T3", "status": "blocked", "note": "aguardando confirmar a chave natural do pedido"}),
    (150, {"type": "note", "agent": "coordinator", "text": "Pergunta enviada ao operador: a chave é (pedido_id, item_seq)?"}),
    (170, {"type": "task", "task": "T3", "status": "running", "note": "chave confirmada pelo operador"}),
    (185, {"type": "task", "task": "T6", "status": "done", "note": "broadcast de clientes elimina o shuffle"}),
    (200, {"type": "task", "task": "T2", "status": "done"}),
    (215, {"type": "task", "task": "T3", "status": "done"}),
    (222, {"type": "stage", "stage": "validacao"}),
    (224, {"type": "task", "task": "T7", "agent": "pipeline-correctness-reviewer", "status": "running",
           "title": "Revisão independente: perdas, duplicidades e reprocessamento"}),
    (226, {"type": "task", "task": "T8", "agent": "maintainability-reviewer", "status": "running",
           "title": "Revisão de simplicidade e organização dos notebooks"}),
    (240, {"type": "task", "task": "T4", "status": "done", "note": "12 expectativas, 0 falhas nos dados sintéticos"}),
    (262, {"type": "task", "task": "T8", "status": "done", "note": "2 sugestões aplicadas"}),
    (280, {"type": "task", "task": "T7", "status": "done", "note": "idempotência confirmada com reexecução"}),
    (286, {"type": "stage", "stage": "consolidacao"}),
    (300, {"type": "stage", "stage": "entrega"}),
    (306, {"type": "run.end", "status": "done", "summary": "3 notebooks, 1 Job e 12 testes entregues"}),
]


def demo_events(stop_at: float = 1.0, base: datetime | None = None, run_id: str | None = None,
                scale: float = 1.0) -> list[dict[str, Any]]:
    total = DEMO_SCRIPT[-1][0]
    limit = total * stop_at
    base = base or utc_now() - timedelta(seconds=limit * scale)
    rid = run_id or new_run_id(base)
    out = []
    for offset, ev in DEMO_SCRIPT:
        if offset > limit:
            break
        out.append({"v": SCHEMA, "ts": iso(base + timedelta(seconds=offset * scale)), "run": rid, **ev})
    return out


def demo_frames(count: int = 24) -> list[dict[str, Any]]:
    """Estados prontos de uma missão simulada (o painel usa quando está sem servidor)."""
    base = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    full = demo_events(1.0, base=base, run_id="demo", scale=6)
    total = DEMO_SCRIPT[-1][0] * 6
    frames = []
    for i in range(1, count + 1):
        cut = base + timedelta(seconds=total * i / count)
        evs = [e for e in full if parse_ts(e["ts"]) <= cut]
        frames.append(build_state(evs, now=cut))
    return frames


def run_demo(live: bool, speed: float) -> int:
    if not live:
        for ev in demo_events(0.62):
            path = events_file()
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        print("Missão de demonstração registrada (parada na etapa de execução). Abra o painel para ver.")
        return 0
    rid = new_run_id(utc_now())
    print("Reproduzindo uma missão simulada no painel (Ctrl+C para interromper)...", flush=True)
    last = 0
    try:
        for offset, ev in DEMO_SCRIPT:
            time.sleep(max(0.0, (offset - last) / max(speed, 0.1)))
            last = offset
            append({"run": rid, **ev})
            print(f"  {ev['type']:<9} {ev.get('task') or ev.get('stage') or ''} {ev.get('status', '')}", flush=True)
    except KeyboardInterrupt:
        append({"type": "run.end", "run": rid, "status": "cancelled", "summary": "demonstração interrompida"})
    return 0


# ---------------------------------------------------------------- exportação estática

def export_html(dest: Path, port: int | None = None) -> Path:
    """Gera o painel como arquivo único: conecta ao servidor local se estiver no ar; senão, mostra a demonstração."""
    cfg = {"mode": "file", "server": f"http://127.0.0.1:{port or known_port()}", "demo": demo_frames(),
           "snapshot": build_state()}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_panel(cfg), encoding="utf-8")
    return dest


def prune(keep: int) -> int:
    events = read_events()
    runs = fold(events)
    ordered = sorted(runs.values(), key=lambda r: r["started"], reverse=True)
    keep_ids = {r["id"] for r in ordered[:keep]} | {r["id"] for r in ordered if r["status"] == "active"}
    kept = [e for e in events if e.get("run") in keep_ids]
    tmp = events_file().with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in kept), encoding="utf-8")
    os.replace(tmp, events_file())
    print(f"Mantidas {len(keep_ids)} missões; {len(events) - len(kept)} eventos removidos.")
    return 0


def auto_prune() -> None:
    try:
        if events_file().stat().st_size > MAX_EVENTS_BYTES:
            prune(40)
    except OSError:
        pass


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="team_board.py", description="Painel em tempo real da equipe Master Data Engineer")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start", help="Inicia uma missão (uma ativação da equipe).")
    p.add_argument("--mode", required=True, help="construir | revisar | depurar")
    p.add_argument("--title", required=True)
    p.add_argument("--project", default="", help="nome ou pasta do projeto (só o nome é guardado)")
    p.add_argument("--host", default="", help="claude | codex")

    p = sub.add_parser("stage", help="Marca a etapa atual da missão.")
    p.add_argument("stage", help=", ".join(STAGE_KEYS))
    p.add_argument("--done", action="store_true", help="marca a etapa como concluída sem abrir a próxima")
    p.add_argument("--note", default="")
    p.add_argument("--run")

    p = sub.add_parser("task", help="Cria ou atualiza a tarefa de um agente.")
    p.add_argument("task_id", help="identificador curto, ex.: T1")
    p.add_argument("--agent", help="ex.: sql-data-modeler (ou coordinator)")
    p.add_argument("--status", default="running", help=", ".join(TASK_STATUSES))
    p.add_argument("--title", default="")
    p.add_argument("--note", default="")
    p.add_argument("--run")

    p = sub.add_parser("note", help="Registra um aviso no feed da missão.")
    p.add_argument("text")
    p.add_argument("--agent", default="coordinator")
    p.add_argument("--run")

    p = sub.add_parser("finish", help="Encerra a missão.")
    p.add_argument("--status", default="done", choices=["done", "failed", "cancelled"])
    p.add_argument("--summary", default="")
    p.add_argument("--run")

    sub.add_parser("hook", help="Entrada para os hooks do Claude Code (lê JSON do stdin).")
    p = sub.add_parser("serve", help="Sobe o painel em primeiro plano.")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--open", action="store_true")
    p = sub.add_parser("ensure", help="Garante o painel no ar (em segundo plano) e mostra o endereço.")
    p.add_argument("--open", action="store_true")
    p.add_argument("--port", type=int, default=None)
    sub.add_parser("stop", help="Para o painel em segundo plano.")
    p = sub.add_parser("status", help="Mostra a missão ativa em texto.")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("demo", help="Registra uma missão simulada.")
    p.add_argument("--live", action="store_true", help="reproduz ao vivo, evento a evento")
    p.add_argument("--speed", type=float, default=4.0, help="velocidade da reprodução ao vivo (padrão 4x)")
    p = sub.add_parser("export", help="Gera o painel como um arquivo HTML único.")
    p.add_argument("dest", nargs="?", default=None)
    p = sub.add_parser("prune", help="Mantém só as missões mais recentes.")
    p.add_argument("--keep", type=int, default=30)

    args = ap.parse_args(argv)

    if args.cmd == "hook":
        try:
            handle_hook(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
        except Exception:  # noqa: BLE001  hook nunca pode atrapalhar o agente
            pass
        return 0

    try:
        if args.cmd == "start":
            auto_prune()
            now = utc_now()
            rid = new_run_id(now)
            project = args.project
            if project and (os.sep in project or "/" in project):
                project = Path(project).name
            host = args.host.strip().lower()
            if not host:
                host = "codex" if os.environ.get("CODEX_HOME") or os.environ.get("CODEX_SANDBOX") else "claude"
            append({"type": "run.start", "run": rid, "mode": norm_mode(args.mode), "title": clean(args.title, 160),
                    "project": clean(project, 80), "host": clean(host, 20)}, now)
            print(rid)
        elif args.cmd == "stage":
            ev = {"type": "stage", "run": resolve_run(args.run), "stage": norm_stage(args.stage),
                  "note": clean(args.note)}
            if args.done:
                ev["status"] = "done"
            append(ev)
        elif args.cmd == "task":
            ev = {"type": "task", "run": resolve_run(args.run), "task": clean(args.task_id, 24),
                  "status": norm_status(args.status), "source": "coordinator"}
            if args.agent:
                agent = norm_agent(args.agent)
                if agent not in AGENT_KEYS:
                    raise ValueError(f"Agente desconhecido: {args.agent}. Use: {', '.join(sorted(AGENT_KEYS))}")
                ev["agent"] = agent
            if args.title:
                ev["title"] = clean(args.title, 160)
            if args.note:
                ev["note"] = clean(args.note)
            append(ev)
        elif args.cmd == "note":
            append({"type": "note", "run": resolve_run(args.run), "agent": norm_agent(args.agent),
                    "text": clean(args.text)})
        elif args.cmd == "finish":
            append({"type": "run.end", "run": resolve_run(args.run), "status": args.status,
                    "summary": clean(args.summary, 200)})
        elif args.cmd == "serve":
            return serve(args.port or known_port(), args.open)
        elif args.cmd == "ensure":
            return ensure(args.open, args.port)
        elif args.cmd == "stop":
            return stop()
        elif args.cmd == "status":
            state = build_state()
            if args.json:
                print(json.dumps(state["run"], ensure_ascii=False, indent=2))
                return 0
            run = state["run"]
            if not run:
                print("Nenhuma missão registrada ainda.")
                return 0
            print(f"{run['title']}  [{run['mode_label']}]  status={run['status']}  progresso={int(run['progress'] * 100)}%")
            print(f"Etapa atual: {dict(STAGES).get(run['current_stage'] or '', '—')}")
            for a in run["agents"]:
                if a["status"] != "idle":
                    print(f"  {a['name']:<24} {a['status']:<8} {a['task_title']}")
        elif args.cmd == "demo":
            return run_demo(args.live, args.speed)
        elif args.cmd == "export":
            dest = Path(args.dest) if args.dest else app_home() / "painel.html"
            print(export_html(dest))
        elif args.cmd == "prune":
            return prune(args.keep)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
