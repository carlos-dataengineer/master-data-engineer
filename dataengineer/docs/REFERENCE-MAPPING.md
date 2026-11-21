# Como os modelos de referência foram aproveitados

Esta adaptação aproveita princípios e padrões transferíveis para Engenharia de Dados, sem copiar cegamente o comportamento dos modelos.

| Modelo | Padrão aproveitado | Adaptação |
|---|---|---|
| Pstack | Skill-orquestradora, playbooks, planejamento e delegação | Uma skill de entrada roteia para três fluxos de dados; o coordenador sintetiza resultados. |
| Thermos | Revisões independentes de corretude e qualidade estrutural | Revisão de pipelines inclui contratos, incrementalidade, idempotência, duplicidades, segurança, custo e operação. |
| Ponytail | Simplicidade, causa raiz, validação e adaptadores finos | Evita frameworks desnecessários e mantém a implementação alinhada aos padrões do projeto. |

## O que não foi importado

- Modelos ou comandos exclusivos do Cursor que não existem nos hosts alvo.
- Regras de front-end, TypeScript/React, UI ou desenvolvimento web sem relação com pipelines.
- Nomes fixos de modelos, benchmarks ou alegações de performance dos projetos de origem.
- Suposições de que toda execução de pipeline é segura ou autorizada.

## Princípios específicos de dados

- Conhecer fonte, destino, grain, chaves e semântica antes de implementar.
- Preservar comportamento full/incremental, CDC, late-arriving data, deduplicação e reprocessamento.
- Verificar idempotência e retries antes de sugerir MERGE, append ou overwrite.
- Tratar schema evolution explicitamente e conforme a versão do runtime.
- Nunca expor credenciais ou dados sensíveis.
- Separar validação local de execução real no workspace Databricks.
