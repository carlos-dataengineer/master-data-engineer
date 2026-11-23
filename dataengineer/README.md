# DataEngineer — equipe de Engenharia de Dados para Databricks

Versão: 0.3.0

A equipe é coordenada por uma skill principal e especializada em construir, revisar e depurar pipelines de dados no Databricks. Python, PySpark e SQL são as linguagens prioritárias.

## Invocação

- Claude Code: /dataengineer
- Codex: $dataengineer ou /skills e selecionar dataengineer

A skill pergunta qual dos três modos será executado: construção de pipeline do zero, revisão de pipeline existente ou correção de bugs/debugging. Não deve iniciar alterações antes de entender o modo e o contexto.

## Instalação

Use o instalador da raiz do repositório (um comando, Claude Code e Codex):

```powershell
irm https://raw.githubusercontent.com/carlos-dataengineer/master-data-engineer/main/install.ps1 | iex
```

```bash
curl -fsSL https://raw.githubusercontent.com/carlos-dataengineer/master-data-engineer/main/install.sh | bash
```

A instalação também gera o Painel da equipe (`~/MasterDataEngineer/painel.html`) e o abre em http://127.0.0.1:47821. O antigo `tools/install-dataengineer.ps1` continua funcionando e repassa os parâmetros para o novo instalador.

A instalação não executa pipelines, não acessa workspaces Databricks, não cria tabelas e não altera permissões.

## Painel da equipe

`skills/dataengineer/scripts/team_board.py` registra missão, etapas e tarefas de cada agente; `assets/painel.html` mostra tudo ao vivo. Veja ../docs/painel.md.

## Aprendizado contextual persistente

A versão 0.2.0 inclui Contextual Learning Engine. Ele mantém memória local por operador e separa memórias técnicas por projeto. Claude Code e Codex sob a mesma conta do sistema operacional compartilham a memória do operador; memórias específicas de um projeto não são recuperadas em outro.

Isso não é fine-tuning nem alteração dos pesos do modelo. É memória externa estruturada, recuperada quando relevante. Usa SQLite e biblioteca padrão Python 3.10+, fora do repositório. Não possui telemetria, rede ou sincronização automática. SQLite não é criptografado automaticamente; não armazene segredos ou informações sensíveis. Trechos recuperados podem ser enviados ao provedor como parte do contexto do prompt.

Consulte skills/dataengineer/references/CONTEXTUAL-LEARNING.md para regras, comandos e limites.
