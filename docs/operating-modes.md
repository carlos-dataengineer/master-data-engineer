# Modos de operação

Toda chamada da skill pergunta qual dos três modos será executado. A equipe aguarda a escolha antes de iniciar alterações.

## 1. Construção de pipeline

1. Capturar objetivo, fontes, destinos, granularidade, chaves, volume, frequência, SLA, regras de negócio e ambiente.
2. Inspecionar estruturas, convenções e contratos já existentes.
3. Definir arquitetura e estratégia de carga (full, incremental, CDC, batch ou streaming conforme aplicável).
4. Delegar implementação para PySpark/Python e/ou SQL.
5. Definir testes de qualidade, integridade, idempotência e reprocessamento.
6. Revisar corretude e manutenção; medir performance se houver hipótese ou risco.
7. Entregar código, documentação, testes, riscos e o que foi efetivamente validado.

## 2. Revisão de pipeline existente

1. Identificar o escopo e entender o comportamento esperado.
2. Inspecionar dependências, schemas, grain, chaves e estratégia de carga.
3. Executar revisões independentes de corretude e manutenibilidade.
4. Acionar segurança, qualidade e performance de acordo com o risco.
5. Reportar achados priorizados com evidência, cenário de reprodução, impacto e recomendação.
6. Não alterar código na revisão, salvo se o operador solicitar também a correção.

## 3. Bug / debugging

1. Capturar erro, logs sanitizados, execução e comportamento esperado/observado.
2. Localizar a primeira divergência na cadeia de dados.
3. Reproduzir o problema quando possível e separar fatos de hipóteses.
4. Corrigir a causa raiz com a menor mudança correta.
5. Criar ou executar teste de regressão.
6. Revisar efeitos colaterais e resumir evidências e limitações.

## Guardrails comuns

- Não presumir nomes de catálogos, schemas, tabelas, colunas, runtime ou regras de negócio.
- Não executar jobs de produção, deploys ou operações destrutivas sem autorização explícita.
- Não afirmar que uma execução Databricks foi validada sem acesso e evidência no workspace correspondente.
- Proteger credenciais e dados sensíveis.
