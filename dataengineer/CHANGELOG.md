# Changelog

## 0.2.0 — aprendizado contextual local

- Adicionado Contextual Learning Engine com SQLite e biblioteca padrão Python.
- Memória persistente entre sessões, com escopo por operador e contexto isolado por projeto.
- Adicionados comandos para status, recuperação, registro, listagem, confirmação, rejeição, exclusão e exportação.
- Memórias inferidas ficam como candidatas e não são aplicadas até confirmação.
- Adicionadas regras de privacidade, isolamento, prevenção de armazenamento de credenciais e política de uso nos oito agentes.
- Memória armazenada fora do pacote e dos repositórios; nenhum dado contextual é distribuído no ZIP.
- Documentada a distinção entre memória contextual e treinamento/fine-tuning do modelo.

## 0.1.0 — primeira estrutura

- Criada a skill central `dataengineer` com escolha obrigatória entre construir, revisar e depurar.
- Criados oito perfis especializados para Claude Code e Codex.
- Adicionados manifestos de plugin para os dois ambientes.
- Documentados os playbooks, a arquitetura, critérios técnicos e a origem dos modelos.
- Adicionado instalador PowerShell com instalação global/projeto e proteção contra sobrescrita acidental.
- Incluídas verificações estáticas do pacote.
