# Como contribuir

Obrigado pelo interesse! O Master Data Engineer é focado **somente em Engenharia de Dados no Databricks** (Python, PySpark e SQL). Contribuições fora desse escopo provavelmente não serão aceitas.

## Antes de abrir um PR

1. Abra uma *issue* descrevendo o problema ou a ideia (use os modelos).
2. Crie uma branch a partir de `main`: `feat/...`, `fix/...` ou `docs/...`.
3. Mantenha a mudança pequena e com um único objetivo.

## Estrutura

| Pasta | O que é |
|---|---|
| `dataengineer/skills/dataengineer/` | A skill coordenadora: `SKILL.md`, scripts (`contextual_memory.py`, `team_board.py`) e o painel (`assets/painel.html`). |
| `dataengineer/agents/` | Os 8 agentes no formato do Claude Code (`.md`). |
| `dataengineer/.codex/agents/` | Os mesmos 8 agentes no formato do Codex (`.toml`). **Mantenha os dois formatos em sincronia.** |
| `scripts/install.py` | Núcleo do instalador (chamado por `install.sh` e `install.ps1`). |
| `tests/`, `dataengineer/tests/` | Testes (somente biblioteca padrão). |
| `docs/` | Documentação e capturas de tela. |

## Rodando os testes

Requer Python 3.11+ para o validador (usa `tomllib`); a ferramenta em si roda em 3.10+.

```bash
python dataengineer/tests/validate_package.py
python -m unittest discover -s dataengineer/tests -p "test_*.py"
python -m unittest discover -s tests -p "test_*.py"
```

Os testes do instalador usam uma pasta pessoal falsa: nada é instalado no seu Claude Code ou Codex.

## Capturas de tela

Se mudar o painel, regenere as imagens do README:

```bash
pip install playwright
python scripts/screenshots.py
```

## Regras

- Sem dependências externas nos scripts que vão para a máquina do usuário (somente biblioteca padrão).
- Nada de telemetria, chamadas de rede ou envio de dados. O painel escuta apenas em `127.0.0.1`.
- Nunca inclua segredos, dados reais, nomes de empresas ou caminhos pessoais em exemplos, testes ou capturas.
- Atualize o `CHANGELOG.md` e, se mudar a versão, o arquivo `VERSION` e os manifestos (`plugin.json`, `marketplace.json`).
- Commits no estilo *Conventional Commits* (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
