# DataEngineer — equipe de Engenharia de Dados para Databricks

Versão: 0.2.0

A equipe é coordenada por uma skill principal e especializada em construir, revisar e depurar pipelines de dados no Databricks. Python, PySpark e SQL são as linguagens prioritárias.

## Invocação

- Claude Code: /dataengineer
- Codex: $dataengineer ou /skills e selecionar dataengineer

A skill pergunta qual dos três modos será executado: construção de pipeline do zero, revisão de pipeline existente ou correção de bugs/debugging. Não deve iniciar alterações antes de entender o modo e o contexto.

## Instalação

Abra o PowerShell nesta pasta e execute:

```powershell
.\tools\install-dataengineer.ps1 -Scope User
```

Para instalar em um projeto específico:

```powershell
.\tools\install-dataengineer.ps1 -Scope Project -ProjectPath "C:\caminho\do\projeto"
```

Por padrão, o instalador não sobrescreve instalações existentes. Use -Overwrite conscientemente.

A instalação não executa pipelines, não acessa workspaces Databricks, não cria tabelas e não altera permissões.

## Aprendizado contextual persistente

A versão 0.2.0 inclui Contextual Learning Engine. Ele mantém memória local por operador e separa memórias técnicas por projeto. Claude Code e Codex sob a mesma conta do sistema operacional compartilham a memória do operador; memórias específicas de um projeto não são recuperadas em outro.

Isso não é fine-tuning nem alteração dos pesos do modelo. É memória externa estruturada, recuperada quando relevante. Usa SQLite e biblioteca padrão Python 3.10+, fora do repositório. Não possui telemetria, rede ou sincronização automática. SQLite não é criptografado automaticamente; não armazene segredos ou informações sensíveis. Trechos recuperados podem ser enviados ao provedor como parte do contexto do prompt.

Consulte skills/dataengineer/references/CONTEXTUAL-LEARNING.md para regras, comandos e limites.
