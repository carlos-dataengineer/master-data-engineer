# Arquitetura da equipe DataEngineer

## Princípio central

Uma única skill de entrada coordena os especialistas e seleciona playbooks de acordo com o modo escolhido. O comportamento é compartilhado entre Claude Code e Codex; adaptadores e descoberta de agentes variam por host.

## Fluxo de alto nível

```text
/dataengineer (Claude) ou $dataengineer (Codex)
                    |
                    v
        Perguntar o modo de trabalho
          /        |         \
       Criar     Revisar    Depurar
          \        |         /
           v       v        v
        Entender contexto e contratos
                    |
                    v
        Selecionar especialistas relevantes
                    |
                    v
       Analisar / planejar / implementar
                    |
                    v
    Verificação + revisão independente
                    |
                    v
        Consolidar evidências e entrega
```

## Papéis

- Coordenador: entrada única, entendimento, planejamento, delegação, controle de conflitos e consolidação.
- Especialistas: arquitetura, PySpark, SQL, qualidade, performance, segurança e revisões independentes.
- Contextual Learning Engine: memória local do operador, com contextos separados por projeto.

O coordenador escolhe a menor composição que cubra os riscos da tarefa. Um único agente escreve em cada conjunto de arquivos. Revisores trabalham em leitura. Se o host não disponibilizar subagentes, as análises são executadas sequencialmente e essa limitação deve ser informada.

## Limites

Não se presume que todo projeto deva usar Lakeflow Declarative Pipelines, Jobs com notebooks, dbt ou uma arquitetura específica. A escolha depende do contexto e dos requisitos. Python/PySpark e SQL são o foco; configurações auxiliares podem ser usadas quando necessárias.
