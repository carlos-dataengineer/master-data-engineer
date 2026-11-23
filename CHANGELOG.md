# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões seguem [SemVer](https://semver.org/lang/pt-BR/).

## 0.3.0 — painel da equipe e instalação com um comando

- **Painel da equipe em tempo real** (`team_board.py` + `assets/painel.html`): missão ativa, 8 etapas, o que cada agente está fazendo agora, quadro de tarefas, linha do tempo por agente, histórico de missões, feed ao vivo, tema claro/escuro, modo TV e atalhos de teclado.
- Servidor local somente leitura em `127.0.0.1:47821`, com atualização por Server-Sent Events; arquivo `painel.html` autônomo que conecta ao servidor ou mostra a demonstração.
- **Hooks do Claude Code**: início e fim de cada subagente registrados automaticamente no painel.
- Protocolo do painel na skill: `start`, `stage`, `task`, `note`, `finish`; `/dataengineer painel` só abre o painel.
- **Instalador de um comando** (`install.ps1` e `install.sh` → `scripts/install.py`): Claude Code e Codex, escopo de usuário ou de projeto, preserva skills/agentes de outras origens, guarda cópia do `settings.json`, desinstala de forma limpa.
- A instalação gera a ferramenta (`~/MasterDataEngineer/painel.html`), o atalho **Abrir painel** e já abre o painel no navegador.
- Metadados do Codex (`agents/openai.yaml`) e marketplace de plugins do Claude Code (`.claude-plugin/marketplace.json`).
- Estrutura de repositório público: CI em Windows/macOS/Linux, modelos de issue e PR, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, `.editorconfig`, `.gitattributes`, release por tag.
- Testes novos: painel (fluxo, hooks, API, CORS, segredos) e instalador (instalar, reinstalar, desinstalar, preservar arquivos de terceiros, escopo de projeto).

## 0.2.0 — aprendizado contextual local

- Adicionado Contextual Learning Engine com SQLite e biblioteca padrão Python.
- Memória persistente entre sessões, com escopo por operador e contexto isolado por projeto.
- Adicionados comandos para status, recuperação, registro, listagem, confirmação, rejeição, exclusão e exportação.
- Memórias inferidas ficam como candidatas e não são aplicadas até confirmação.
- Adicionadas regras de privacidade, isolamento e prevenção de armazenamento de credenciais.
- Memória armazenada fora do pacote e dos repositórios; nenhum dado contextual é distribuído no pacote.
- Documentada a distinção entre memória contextual e treinamento/fine-tuning.

## 0.1.0 — primeira estrutura

- Criada skill central dataengineer com escolha obrigatória entre construção, revisão e debugging.
- Criados oito perfis especializados para Claude Code e Codex.
- Adicionados manifestos para os dois ambientes.
- Documentados playbooks, arquitetura, critérios técnicos e origem dos modelos.
- Adicionado instalador PowerShell e verificações estáticas.
