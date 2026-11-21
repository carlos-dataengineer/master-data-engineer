# Checklist técnico de pipelines

Aplicar de acordo com o caso; não transformar a lista inteira em burocracia obrigatória.

## Contrato e semântica
- [ ] Fonte, destino, owner e propósito conhecidos.
- [ ] Granularidade (grain) explicitada.
- [ ] Chaves naturais/técnicas e critérios de unicidade definidos.
- [ ] Tipos, nulabilidade, timezone e semântica de colunas compreendidos.
- [ ] Joins avaliados quanto a cardinalidade, chaves ausentes e multiplicação/perda de linhas.
- [ ] Regras de negócio e tratamento de dados inválidos documentados.

## Ingestão e incrementalidade
- [ ] Modo full/incremental/CDC definido.
- [ ] Watermark, cursor ou coluna de atualização definido quando necessário.
- [ ] Late-arriving data, reprocessamento e backfill considerados.
- [ ] Deduplicação e ordenação determinística definidas quando necessárias.
- [ ] Retry/re-run seguro e idempotência avaliados.
- [ ] MERGE, append, overwrite ou replace escolhidos de forma compatível com semântica e concorrência.
- [ ] Schema evolution explícito e compatível com o runtime.

## Qualidade e validação
- [ ] Schema e tipos validados.
- [ ] Unicidade, nulos, integridade e regras de domínio testados conforme aplicável.
- [ ] Contagens, intervalos e reconciliação de linhas avaliados.
- [ ] Freshness/SLA e atrasos considerados.
- [ ] Testes de regressão cobrem o defeito ou regra principal.
- [ ] Testes usam dados sintéticos ou sanitizados quando possível.

## Performance e operação
- [ ] Volume, frequência e latência esperada compreendidos.
- [ ] Shuffle, skew, particionamento, broadcast e plano físico analisados quando relevante.
- [ ] Escrita/compactação/pequenos arquivos considerados conforme carga real.
- [ ] Orquestração, dependências, retries, timeout e alertas avaliados.
- [ ] Métricas, logs e rastreabilidade permitem investigar falhas.
- [ ] Custo e tamanho do compute são proporcionais ao SLA.

## Segurança e governança
- [ ] Segredos obtidos por mecanismo aprovado; nunca hardcoded ou impressos em logs.
- [ ] Permissões de leitura/escrita seguem menor privilégio.
- [ ] Catálogo/schema/tabelas e classificação de dados são apropriados.
- [ ] Dados sensíveis não são copiados para exemplos, prompts ou logs não autorizados.
- [ ] Acesso e alterações de permissões exigem autorização explícita.

## Entrega
- [ ] Instruções de execução e dependências registradas.
- [ ] Evidências de teste e limitações apresentadas.
- [ ] Nenhuma execução em produção ou operação destrutiva sem autorização.
