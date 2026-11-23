# Política de segurança

## Versões suportadas

| Versão | Suporte |
|---|---|
| 0.3.x | ✅ |
| < 0.3 | ❌ |

## Como relatar uma vulnerabilidade

**Não abra uma issue pública.** Use o recurso [*Report a vulnerability*](https://github.com/carlos-dataengineer/master-data-engineer/security/advisories/new) do GitHub (aba **Security**). Descreva o problema, como reproduzir e o impacto. A resposta inicial acontece em até 7 dias.

## O que o projeto faz e não faz

- **Instalador:** copia arquivos para `~/.claude`, `~/.agents`, `~/.codex` e `~/MasterDataEngineer`. No Claude Code, adiciona dois hooks (`PreToolUse`/`PostToolUse` para a ferramenta de subagentes) ao `settings.json`, depois de salvar uma cópia em `settings.json.bak-mde`. Use `--no-hooks` para não alterar o `settings.json`.
- **Painel:** servidor HTTP **somente leitura** que escuta apenas em `127.0.0.1`. Não aceita escrita pela rede e só libera leitura entre origens para o próprio arquivo local do painel (origem `null`).
- **Eventos do painel:** ficam em `~/MasterDataEngineer/board/events.jsonl`, só com títulos curtos das tarefas. Textos que parecem credenciais são substituídos por um aviso antes de serem gravados.
- **Memória contextual:** SQLite local, fora do repositório, sem criptografia automática. Não guarde segredos nem dados pessoais.
- **Sem telemetria:** nenhum script faz chamadas de rede, exceto o instalador ao baixar este repositório do GitHub.
- **Databricks:** a equipe não executa Jobs, não altera tabelas e não muda permissões sem autorização explícita do operador.
