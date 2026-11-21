# Modos de operação

Toda chamada da skill pergunta qual dos três modos será executado e aguarda a resposta antes de fazer alterações.

## 1. Construção de pipeline

1. Capturar objetivo, fontes, destinos, granularidade, chaves, volume, frequência, SLA, regras e ambiente.
2. Inspecionar convenções e contratos existentes.
3. Definir arquitetura e estratégia de carga (full, incremental, CDC, batch ou streaming).
4. Delegar implementação para PySpark/Python e/ou SQL.
5. Definir testes de qualidade, integridade, idempotência e reprocessamento.
6. Revisar corretude e manutenção; medir performance quando houver hipótese ou risco.
7. Entregar código, documentação, testes, riscos e evidências.

## 2. Revisão de pipeline existente

1. Identificar o escopo e comportamento esperado.
2. Inspecionar dependências, schemas, grain, chaves e estratégia de carga.
3. Executar revisões independentes de corretude e manutenibilidade.
4. Acionar segurança, qualidade e performance conforme o risco.
5. Reportar achados com severidade, evidência, impacto e recomendação.
6. Não alterar código na revisão, salvo pedido explícito de correção.

## 3. Bug / debugging

1. Capturar erro, logs sanitizados, execução e comportamento esperado/observado.
2. Localizar a primeira divergência na cadeia de dados.
3. Reproduzir quando possível e separar fatos de hipóteses.
4. Corrigir a causa raiz com a menor mudança correta.
5. Criar ou executar teste de regressão.
6. Revisar efeitos colaterais e relatar evidências e limitações.

## Guardrails

- Não presumir catálogos, schemas, tabelas, colunas, runtime ou regras de negócio.
- Não executar jobs de produção, deploys ou operações destrutivas sem autorização.
- Não afirmar validação no Databricks sem acesso e evidência do workspace.
- Proteger credenciais e dados sensíveis.
