# DataEngineer — equipe de Engenharia de Dados para Databricks

Versão: 0.2.0

## Objetivo

Uma equipe de agentes coordenada por uma skill principal, especializada em construir, revisar e depurar pipelines de dados em ambientes Databricks. Python/PySpark e SQL são as linguagens prioritárias.

## Invocação

- **Claude Code:** `/dataengineer`
- **Codex:** `$dataengineer` ou `/skills` e selecionar `dataengineer`

A skill pergunta qual dos três modos será executado sempre que for chamada: construção, revisão ou debugging. A equipe não deve iniciar alterações antes de entender o modo e o contexto.

## Instalação

Abra o PowerShell nesta pasta e execute:

```powershell
.\tools\install-dataengineer.ps1 -Scope User
```

Para instalar em um projeto específico:

```powershell
.\tools\install-dataengineer.ps1 -Scope Project -ProjectPath "C:\caminho\do\projeto"
```

## Aprendizado contextual

A versão 0.2.0 inclui uma memória local persistente por operador, com contextos separados por projeto. Ela usa SQLite e não realiza fine-tuning nem altera os pesos do modelo. Memórias ainda não confirmadas não são aplicadas automaticamente. Consulte `skills/dataengineer/references/CONTEXTUAL-LEARNING.md`.

A instalação não conecta automaticamente a um workspace Databricks, não executa Jobs, não cria tabelas e não altera permissões. A execução real depende das permissões e ferramentas disponíveis no ambiente.
