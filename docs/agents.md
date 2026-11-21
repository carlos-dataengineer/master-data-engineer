# Catálogo de agentes

O coordenador `dataengineer` decide quais perfis participarão de cada trabalho. Os oito agentes não são convocados automaticamente em toda tarefa.

| Agente | Especialidade | Entregas típicas |
|---|---|---|
| Data Architect | Requisitos, arquitetura e contratos de dados | Fluxo, contratos, grain, dependências, decisões e riscos |
| Databricks / PySpark Engineer | Python, PySpark e recursos Databricks | Implementação, notebooks, Jobs, transformação e depuração |
| SQL Data Modeler | SQL, Databricks SQL e modelagem | Consultas, joins, chaves, grain e modelos analíticos |
| Data Quality Engineer | Qualidade e testes de dados | Regras, reconciliação, integridade e regressão |
| Performance & Cost Engineer | Spark e custos de execução | Diagnóstico de plano, shuffle, skew, particionamento e medição |
| Governance & Security Reviewer | Segurança e governança de dados | Unity Catalog, menor privilégio, segredos e exposição |
| Pipeline Correctness Reviewer | Corretude independente | Achados funcionais, semântica de dados, regressões e evidências |
| Maintainability Reviewer | Manutenibilidade e simplicidade | Duplicação, complexidade acidental, legibilidade e fronteiras |

```mermaid
flowchart TB
  CO[Coordenador]
  CO --> ARC[Arquitetura]
  CO --> DEV[Implementação]
  CO --> QUAL[Qualidade]
  CO --> PERF[Performance]
  CO --> GOV[Governança]
  CO --> REV[Revisão independente]
  ARC --> A1[Data Architect]
  DEV --> A2[Databricks / PySpark]
  DEV --> A3[SQL Modeler]
  QUAL --> A4[Data Quality]
  PERF --> A5[Performance & Cost]
  GOV --> A6[Governance & Security]
  REV --> A7[Pipeline Correctness]
  REV --> A8[Maintainability]
  A1 --> DONE[Consolidação e evidências]
  A2 --> DONE
  A3 --> DONE
  A4 --> DONE
  A5 --> DONE
  A6 --> DONE
  A7 --> DONE
  A8 --> DONE
```

## Responsabilidade final

Os especialistas entregam análises e mudanças delimitadas. O coordenador consolida divergências, verifica evidências, comunica limitações e responde pelo resultado apresentado ao operador.
