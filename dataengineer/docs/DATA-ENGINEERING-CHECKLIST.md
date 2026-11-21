# Checklist técnico de pipelines

Aplicar de acordo com o caso; não transformar a lista inteira em burocracia obrigatória.

## Contrato e semântica
- [ ] Fonte, destino, owner e propósito conhecidos.
- [ ] Granularidade (grain) explicitada.
- [ ] Chaves naturais/técnicas e critérios de unicidade definidos.
- [ ] Tipos, nulabilidade, timezone e semântica compreendidos.
- [ ] Joins avaliados quanto a cardinalidade e multiplicação/perda de linhas.
- [ ] Regras de negócio e tratamento de dados inválidos documentados.

## Ingestão e incrementalidade
- [ ] Modo full/incremental/CDC definido.
- [ ] Watermark/cursor definido quando necessário.
- [ ] Late-arriving data, reprocessamento e backfill considerados.
- [ ] Deduplicação e ordenação determinística definidas quando necessárias.
- [ ] Retry seguro e idempotência avaliados.
- [ ] MERGE, append, overwrite ou replace compatíveis com semântica e concorrência.
- [ ] Schema evolution explícito e compatível com runtime.

## Qualidade e validação
- [ ] Schema e tipos validados.
- [ ] Unicidade, nulos, integridade e regras de domínio testados.
- [ ] Contagens e reconciliação avaliadas.
- [ ] Freshness/SLA considerados.
- [ ] Testes de regressão cobrem a regra principal.
- [ ] Testes usam dados sintéticos ou sanitizados quando possível.

## Performance e operação
- [ ] Volume, frequência e latência compreendidos.
- [ ] Shuffle, skew, particionamento, broadcast e plano físico analisados quando relevante.
- [ ] Pequenos arquivos e escrita considerados conforme carga real.
- [ ] Orquestração, retries, timeout e alertas avaliados.
- [ ] Métricas e logs permitem investigar falhas.
- [ ] Custo de compute é proporcional ao SLA.

## Segurança e entrega
- [ ] Segredos obtidos por mecanismo aprovado; nunca hardcoded/logados.
- [ ] Permissões seguem menor privilégio.
- [ ] Catálogo/schema/tabelas e classificação apropriados.
- [ ] Dados sensíveis não são copiados para exemplos ou logs não autorizados.
- [ ] Nenhuma execução em produção ou operação destrutiva sem autorização.
- [ ] Instruções, evidências de teste e limitações documentadas.
