# Casos de uso

Exemplos de como acionar a equipe e o que esperar. Em todos, a primeira pergunta é o modo; depois a equipe pede só o que falta para decidir com segurança. Os nomes de tabelas são fictícios.

## 1. Construir um pipeline incremental (bronze → silver → gold)

**Você diz:** “Modo 1. Pedidos chegam como JSON em um volume; quero bronze com Auto Loader, silver deduplicada e uma gold diária de vendas por loja.”

**A equipe pergunta:** grain da silver, chave natural, frequência, janela de reprocessamento, chegada tardia, catálogo/schema de destino, consumidores da gold.

**Quem trabalha:** Data Architect (contrato e fluxo) → PySpark (bronze) e SQL Modeler (`MERGE` da silver e gold) em paralelo → Data Quality (expectativas) → Governance (grants e segredos) → Correctness e Maintainability (revisão independente).

**Você recebe:** notebooks/SQL, definição do Job, testes com dados sintéticos, decisões tomadas e o que ainda precisa ser validado no workspace.

**No painel:** 5 a 7 cartões ativos ao longo da missão; uma tarefa pode ficar “Bloqueada” enquanto a equipe espera sua confirmação da chave.

## 2. Migrar uma carga full para incremental/CDC

**Você diz:** “Modo 1. Hoje reprocesso a tabela de clientes inteira todo dia; quero incremental com CDC da origem.”

**Foco:** idempotência, ordem dos eventos, deletes, watermark, backfill e reconciliação entre a versão antiga e a nova.

## 3. Revisar um pipeline antes de produção

**Você diz:** “Modo 2. Revise a pasta `jobs/faturamento/` (diff da branch atual).”

**Quem trabalha:** Pipeline Correctness e Maintainability sempre; Performance e Governance quando o risco justificar.

**Você recebe:** achados ordenados por severidade, cada um com evidência (arquivo/linha), cenário de reprodução, impacto e recomendação, além do que foi e do que não foi verificado. A revisão não altera os arquivos, a menos que você peça.

## 4. Depurar números que não batem

**Você diz:** “Modo 3. A gold de vendas mostra 3% a menos que a origem desde terça.”

**A equipe pede:** run/task ID, etapa, esperado × observado, amostra sanitizada, última alteração.

**Fluxo:** localizar a primeira etapa onde o dado diverge → separar bug de código de problema de origem/permissão/configuração → correção mínima de causa raiz → teste de regressão → evidência antes/depois.

## 5. Job lento ou caro

**Você diz:** “Modo 3. O Job de eventos passou de 20 para 80 minutos.”

**Quem trabalha:** Performance & Cost (plano de execução, shuffle, skew, partições, small files), PySpark e Correctness para garantir que a otimização não muda o resultado.

## 6. Auditoria de governança

**Você diz:** “Modo 2. Verifique permissões, uso de segredos e exposição de dados pessoais nos Jobs do domínio financeiro.”

**Quem trabalha:** Governance & Security, com Maintainability para padronizar o que for corrigido.

## 7. Acompanhar a equipe no telão

Abra o painel, tecle **F** (modo TV) e **1** (visão geral). Cada agente mostra a tarefa atual e há quanto tempo está nela; o feed mostra cada mudança na hora. Para rever uma missão antiga, tecle **4** e clique nela; **A** volta para a ativa.

## O que a equipe não faz

- Não executa Jobs de produção, operações destrutivas, mudanças de permissão ou deploy sem autorização explícita.
- Não afirma que algo rodou no Databricks sem evidência do workspace.
- Não é uma equipe genérica de desenvolvimento (sites, apps, APIs).
