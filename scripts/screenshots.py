"""Gera as capturas de tela do README em docs/images/.

Sobe o painel real numa pasta temporária, registra missões de demonstração e fotografa cada
visão (escuro, claro, celular, ajuda), um GIF da atualização ao vivo e a saída do instalador.
Nada usa dados reais: tudo vem da missão simulada do próprio team_board.py.

Requer: pip install playwright pillow   (usa o Chrome/Edge instalado; ou: python -m playwright install chromium)
Uso:    python scripts/screenshots.py
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from datetime import timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
SCRIPTS = ROOT / "dataengineer" / "skills" / "dataengineer" / "scripts"


def browser(pw):
    for channel in ("chrome", "msedge", None):
        try:
            return pw.chromium.launch(channel=channel, headless=True) if channel else pw.chromium.launch(headless=True)
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("Nenhum Chromium disponível. Instale o Chrome ou rode: python -m playwright install chromium")


def write_events(tb, events):
    path = tb.events_file()
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")


def history_events(tb):
    now = tb.utc_now()
    out = []

    def run(offset_min, mode, title, project, host, steps, summary, status="done"):
        base = now - timedelta(minutes=offset_min)
        rid = tb.new_run_id(base)
        out.append({"v": 1, "ts": tb.iso(base), "type": "run.start", "run": rid, "mode": mode, "title": title,
                    "project": project, "host": host})
        t = base
        for ev in steps:
            t += timedelta(minutes=2)
            out.append({"v": 1, "ts": tb.iso(t), "run": rid, **ev})
        out.append({"v": 1, "ts": tb.iso(t + timedelta(minutes=3)), "type": "run.end", "run": rid,
                    "status": status, "summary": summary})

    run(26 * 60, "revisar", "Revisão do job de faturamento diário", "faturamento", "codex", [
        {"type": "task", "task": "T1", "agent": "pipeline-correctness-reviewer", "status": "done", "title": "Corretude do MERGE"},
        {"type": "task", "task": "T2", "agent": "maintainability-reviewer", "status": "done", "title": "Organização dos notebooks"},
        {"type": "task", "task": "T3", "agent": "performance-cost-engineer", "status": "done", "title": "Plano de execução"},
    ], "4 achados, 1 crítico, com evidências")
    run(50 * 60, "depurar", "Duplicidades na silver de clientes", "crm-lakehouse", "claude", [
        {"type": "task", "task": "T1", "agent": "databricks-pyspark-engineer", "status": "done", "title": "Localizar divergência"},
        {"type": "task", "task": "T2", "agent": "data-quality-engineer", "status": "done", "title": "Teste de regressão"},
    ], "Causa raiz: watermark ausente; corrigido e testado")
    run(75 * 60, "construir", "Ingestão de eventos de app (streaming)", "app-events", "claude", [
        {"type": "task", "task": "T1", "agent": "data-architect", "status": "done", "title": "Contrato do evento"},
        {"type": "task", "task": "T2", "agent": "governance-security-reviewer", "status": "blocked", "title": "Permissões no catálogo"},
    ], "Aguardando acesso ao catálogo de produção", "cancelled")
    return out


def installer_output() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        env = {k: v for k, v in os.environ.items() if k not in ("CODEX_HOME", "DATAENGINEER_HOME")}
        env.update({"HOME": tmp, "USERPROFILE": tmp, "MDE_NO_OPEN": "1", "MDE_NO_SERVER": "1", "NO_COLOR": "1"})
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / "install.py")], env=env,
                           capture_output=True, text=True, encoding="utf-8")
        text = r.stdout
        for variant in {tmp, str(Path(tmp).resolve())}:
            text = text.replace(variant + os.sep, "~/").replace(variant, "~")
        text = text.replace("\\", "/")
        text = text.replace("Painel da equipe: http://127.0.0.1:47821", "Painel da equipe: http://127.0.0.1:47821  (aberto no navegador)")
        return text.strip("\n")


def terminal_html(text: str) -> str:
    def color(line: str) -> str:
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = re.sub(r"^(\s*)✓", r'\1<b style="color:#4ade80">✓</b>', safe)
        safe = re.sub(r"^(\s*)&gt;", r'\1<b style="color:#38bdf8">&gt;</b>', safe)
        safe = re.sub(r"^(\s*)!", r'\1<b style="color:#fbbf24">!</b>', safe)
        safe = safe.replace("Master Data Engineer", '<b style="color:#a5b4fc">Master Data Engineer</b>', 1)
        safe = safe.replace("Pronto.", '<b style="color:#4ade80">Pronto.</b>')
        return safe
    body = "\n".join(color(line) for line in text.splitlines())
    cmd = "irm https://raw.githubusercontent.com/carlos-dataengineer/master-data-engineer/main/install.ps1 | iex"
    return f"""<!doctype html><meta charset=utf-8><body style="margin:0;background:#0b1020;padding:28px">
<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.5);overflow:hidden;max-width:1100px">
<div style="display:flex;gap:7px;padding:11px 14px;background:#111a2e;border-bottom:1px solid #1e293b">
<i style="width:11px;height:11px;border-radius:50%;background:#ef4444"></i><i style="width:11px;height:11px;border-radius:50%;background:#f59e0b"></i><i style="width:11px;height:11px;border-radius:50%;background:#22c55e"></i>
<span style="margin-left:10px;color:#64748b;font:12px Segoe UI,system-ui">PowerShell</span></div>
<pre style="margin:0;padding:18px 20px;color:#cbd5e1;font:13px/1.6 Consolas,ui-monospace,monospace;white-space:pre-wrap"><span style="color:#64748b">PS&gt;</span> {cmd}
  <b style="color:#38bdf8">&gt;</b> Baixando carlos-dataengineer/master-data-engineer (main)
{body}</pre></div></body>"""


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Instale o Playwright: pip install playwright")
    OUT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DATAENGINEER_HOME"] = tmp
        sys.path.insert(0, str(SCRIPTS))
        import team_board as tb

        past = history_events(tb)
        write_events(tb, past + tb.demo_events(0.47, scale=4))
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), tb.BoardHandler)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{port}/"

        with sync_playwright() as pw:
            b = browser(pw)
            ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
            page = ctx.new_page()

            def shot(name, view="overview", theme="dark", full=False, key=None, wait=900):
                page.goto(f"{url}?view={view}&theme={theme}")
                page.wait_for_selector(".mission", timeout=10000)
                if key:
                    page.keyboard.press(key)
                page.wait_for_timeout(wait)
                page.screenshot(path=str(OUT / name), full_page=full)
                print("  ✓", name)

            shot("painel-visao-geral.png", full=True)
            shot("painel-tarefas.png", "tasks")
            shot("painel-linha-do-tempo.png", "timeline")
            shot("painel-historico.png", "history")
            shot("painel-tema-claro.png", theme="light", full=True)
            shot("painel-atalhos.png", key="?")

            mob = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
            mp = mob.new_page()
            mp.goto(f"{url}?view=overview&theme=dark")
            mp.wait_for_selector(".mission")
            mp.wait_for_timeout(800)
            mp.screenshot(path=str(OUT / "painel-celular.png"))
            print("  ✓ painel-celular.png")

            # GIF: a mesma missão avançando, gravada pelo caminho real (arquivo → SSE → navegador)
            try:
                from PIL import Image
            except ImportError:
                Image = None
                print("  ! Pillow ausente: GIF não gerado (pip install pillow)")
            if Image is not None:
                gctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                gp = gctx.new_page()
                base = tb.utc_now() - timedelta(seconds=306 * 4)
                rid = "rdemo-gif"
                frames = []
                cuts = [0.04, 0.16, 0.2, 0.3, 0.4, 0.47, 0.56, 0.66, 0.74, 0.8, 0.9, 0.95, 1.0]
                for i, cut in enumerate(cuts):
                    write_events(tb, past + tb.demo_events(cut, base=base, run_id=rid, scale=4))
                    if i == 0:
                        gp.goto(f"{url}?view=overview&theme=dark")
                        gp.wait_for_selector(".mission")
                    gp.wait_for_timeout(1300)
                    png = gp.screenshot(clip={"x": 0, "y": 0, "width": 1440, "height": 900})
                    frames.append(Image.open(io.BytesIO(png)).convert("RGB").resize((960, 600), Image.LANCZOS))
                pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
                durations = [1100] * (len(pal) - 1) + [3200]
                pal[0].save(OUT / "painel-ao-vivo.gif", save_all=True, append_images=pal[1:], duration=durations,
                            loop=0, optimize=True)
                print("  ✓ painel-ao-vivo.gif")

            term = b.new_context(viewport={"width": 1156, "height": 600}, device_scale_factor=1.5)
            tp = term.new_page()
            tp.set_content(terminal_html(installer_output()))
            box = tp.locator("body > div").bounding_box()
            tp.screenshot(path=str(OUT / "instalacao.png"),
                          clip={"x": 0, "y": 0, "width": 1156, "height": box["y"] + box["height"] + 28})
            print("  ✓ instalacao.png")
            b.close()
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
