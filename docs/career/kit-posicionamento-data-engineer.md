# Kit de posicionamento e divulgação — portfólio Data Engineer

**Data:** 24 de novembro de 2026 (America/Sao_Paulo)
**Idioma:** português (BR), exceto pitch do README, posts, headline e About do LinkedIn — esses vão em inglês.
**Status deste kit:** rascunho operacional. Nada aqui foi publicado, postado ou enviado.

**Regra de honestidade (valer em todo o kit):** o portfólio prova *habilidade e critério de desenho*. Ele **não** conta como anos de experiência comercial em Data Engineering em produção. Não use o projeto para inflar tenure, escala, on-call ou “real-time” que o MVP não entrega.

**Repo:** `github.com/joaquim4lves/pix-data-platform`. Os caminhos de evidência abaixo são **artefatos previstos** no plano do projeto, não pastas já existentes. Ajuste os paths quando a estrutura estiver fechada.

---

## 1. Posicionamento

### One-liner

Tech lead de backend que leva rigor de produção — APIs, ownership e infra como código — para plataformas de dados, com domínio de pagamentos, sem recomeçar a carreira do zero.

### Narrativa central

Joaquim não é um júnior em dados que “fez um curso e um pipeline”. É um engenheiro sênior com mais de 10 anos construindo e liderando sistemas em produção (Python, FastAPI, Django, Node). O movimento para Data Engineer Sênior é uma **expansão do mesmo ofício**: modelar dados, garantir qualidade, automatizar deploys, operar o que quebra e entregar valor para o negócio — agora no recorte analítico (lake, ELT, orquestração, warehouse/marts, dashboards).

O portfólio (“PIX Lake”) é a prova auditável dessa expansão: dados abertos do PIX (Banco Central) chegam em S3, passam por modelagem e testes em dbt, são orquestrados no Airflow, aparecem no Metabase, e a infra AWS sobe com Terraform. O domínio (PIX, fraude, CDC de um merchant simulado) reforça a experiência em fintech e pagamentos.

A frase que o recrutador precisa ouvir em 15 segundos:

> “Eu já opero sistemas em produção há mais de uma década. Este repositório mostra como eu desenho uma plataforma de dados ponta a ponta — com as mesmas exigências de idempotência, teste, observabilidade e infra como código que eu cobro de um backend.”

A frase que ele **não** precisa ouvir: “estou começando em dados” ou “tenho X anos como Data Engineer”.

### Forças para liderar (nessa ordem)

1. **Engenharia de plataforma / sistemas em produção.** Ownership de ponta a ponta, decisão arquitetural documentada (ADRs), hábitos de produção (CI, retries, idempotência, least privilege). Isso diferencia de portfólio-tutorial.
2. **APIs de produção.** FastAPI/Django/Node: contratos, paginação, falhas, retries, integração com sistemas transacionais. A ingestão PIX/BCB e o serviço OLTP+CDC nascem dessa força, não de um script solto.
3. **Ownership.** Tech lead que decompõe problema, fecha fatia, documenta trade-off e entrega algo que outra pessoa consegue rodar. No portfólio: tags por release, README “how to run”, runbook, “what I’d do next”.
4. **Infra como código.** Terraform (S3, IAM, e o que o recorte AWS fechar: Lambda, SQS, Glue/Athena, etc.), Docker, GitHub Actions. Não “cliquei no console”.
5. **Domínio de pagamentos.** PIX, estatísticas de fraude, CDC de pagamentos simulados. Trate como contexto de negócio e modelagem — não como “eu montei o PIX do Banco Central”.

O SQL analítico, o dbt e o Airflow **entram na conversa**, mas como evidência do portfólio (e, no SQL, também como extensão da modelagem que um backend sênior já faz no OLTP). Eles não substituem a história de seniority.

## 2. Pitch do topo do README (inglês)

Três a quatro linhas. Colocar logo abaixo do título, antes do diagrama. Não overclaim.

### Versão principal (recomendada)

Senior backend engineer and tech lead with 10+ years shipping production APIs in Python and Node. This repository is an end-to-end data platform I designed and built: public PIX payments data from Banco Central do Brasil lands in S3, is transformed and tested in dbt, orchestrated in Airflow, and explored in Metabase, with AWS infrastructure in Terraform. It applies production habits — idempotent ingestion, data tests, retries, freshness checks, and infrastructure as code — to an analytical stack in the payments domain.

### Alternativa

I build reliable platforms. After a decade leading backend systems (Python, FastAPI, Django, Node), I built this open data platform around Brazil’s PIX: incremental ingestion from Banco Central APIs into S3, dimensional models and tests in dbt, Airflow DAGs with retries and alerts, Metabase dashboards that answer concrete business questions, and Terraform on AWS. The goal is recruiter-readable, interviewer-auditable proof of data-platform skills — lake, ELT, quality, orchestration, and infra as code.

---

## 3. Plano de divulgação

**Não publicar, postar ou enviar nada a partir deste kit.** Cada post só vai ao ar *depois* da tag/release correspondente existir, com CI verde e o path do README atualizado. Métricas de resultado (runtime, custo, cobertura de testes, freshness) entram só quando forem medidas — até lá, use os placeholders e corte a frase se o número não existir.

Cadência sugerida: um post por fatia entregue, no dia da release. O plano também prevê fatias de SQL dimensional (`v0.2`) e OLTP+CDC (`v0.3`); há rascunhos opcionais no final desta seção.

Audiência dos textos de LinkedIn: internacional (vagas remotas). Por isso estão em inglês. Uma variante curta em PT pode ser útil na rede brasileira.

### 3a. Posts no LinkedIn (um por fatia)

Formato de cada item: gancho, miolo, CTA. Tom de engenheiro sênior, não de “happy to share”. Sempre linkar a tag, não só o repo genérico.

#### 1) Ingestão PIX/BCB → S3 (`v0.1`)

- **Hook:** Public APIs fail in boring ways: pagination, late-arriving pages, and retries that double-write.
- **Gist:** Shipped the first slice of my data-platform portfolio: incremental, idempotent ingestion of public PIX datasets from Banco Central do Brasil into Parquet on S3 (and a local path you can run without a cloud bill). Watermarking, tests, Docker, and a minimal CI path are in the repo. This is open, aggregated official data — not a claim that I operate PIX itself.
- **CTA:** Tag `v0.1` has the ingestor, a sample dataset, and a “how to run” in the README. If you ingest public APIs for a living, I’d value a look at the watermark approach.

#### 2) Modelos e testes dbt (`v0.5`)

- **Hook:** A pipeline that can’t tell you when a grain broke is just a cron job with extra steps.
- **Gist:** Moved the PIX dimensional model into dbt (staging → marts): star schema around payments activity, with tests for uniqueness, not-null, relationships, and freshness, plus published docs. I treated dbt as a project to architect — layers, naming, test strategy — not a pile of SELECT statements. The business questions the marts are meant to answer are listed in the README.
- **CTA:** Docs and models are in the `v0.5` release. Happy to compare notes on test design vs. over-testing a small public dataset.

#### 3) Orquestração Airflow (`v0.6`)

- **Hook:** “It ran on my machine” is not orchestration. Backfills, retries, and a failed freshness check are.
- **Gist:** Wired ingestion → dbt → checks into Airflow DAGs, with retries, alerting, and a short runbook. I am showing the production *patterns* I want to be judged on (idempotency, recoverability, visible failure).
- **CTA:** DAGs and the runbook are in `v0.6`. If you review data-platform portfolios, this is the slice I’d start with.

#### 4) Dashboards Metabase (`v1.0`, ou a tag do dashboard se sair antes do wrap-up)

- **Hook:** If a dashboard can’t answer a question a hiring manager would actually ask, it’s decoration.
- **Gist:** Published Metabase views on top of the PIX marts: volume and average ticket over time, geography, payee sectors, key adoption, and reported fraud vs. transaction volume — plus a comparison against a simulated merchant CDC feed. Each chart maps to a question in the README, not to a KPI I “improved” in a real company.
- **CTA:** The dashboard link and the question list are in the release notes. Critique welcome: which question would you drop, and which one is missing?

#### 5) Infra Terraform (`v0.4`)

- **Hook:** A data platform that only exists in screenshots is a slide deck. I’d rather you run `terraform plan`.
- **Gist:** AWS infra for the lake is in Terraform: layered S3, least-privilege IAM, and the compute/catalog pieces documented in `/infra` (target shape: Lambda, SQS, Glue Catalog, Athena — ship only what actually landed). Includes a cost note and a documented `destroy`. No console clicking as the source of truth.
- **CTA:** Tag `v0.4` has the modules, the architecture diagram, and the cost estimate. I’d like feedback on the IAM boundaries more than on the logo soup.

#### 6) Wrap-up da plataforma (`v1.0`)

- **Hook:** I already knew how to ship backend systems. I wanted a repo a data interviewer could audit in one sitting.
- **Gist:** End-to-end portfolio platform is now tagged `v1.0`: PIX/BCB → S3, dbt models and tests, Airflow, Metabase, Terraform on AWS. I’m a senior backend engineer and tech lead moving into data platform work — this repo is the evidence. README has the diagram, ADRs, how to run it, and an honest “what I’d do next”.
- **CTA:** If you hire or vet remote Senior Data Engineers, the README is written for a five-minute pass. Link in the comments. I’m also glad to walk through trade-offs, not just the stack list.

#### Opcional — se as fatias de SQL e CDC saírem com tag própria

**SQL e modelagem dimensional (`v0.2`)**

- **Hook:** Before I reached for dbt, I wanted the grain and the joins to survive on raw SQL.
- **Gist:** Hand-built a star schema (fact + dimensions) and answered the first business questions with CTEs and window functions in `/sql`, plus an ER diagram. That SQL later becomes dbt — so the model is a decision, not a tool demo.
- **CTA:** `v0.2` has the queries and the diagram. Tell me where you’d change the grain.

**OLTP + CDC (`v0.3`)**

- **Hook:** Public aggregates are useful. The harder pattern is change data from a transactional payments system — even a simulated one.
- **Gist:** Added a small FastAPI + Postgres “merchant” that emits payments, then CDC into the lake, with dedupe/ordering and an ADR for the method chosen. This is a simulated workload to practice the pattern, not production PSP traffic.
- **CTA:** ADR + pipeline in `v0.3`. I’d especially like review on the dedupe rules.

### 3b. LinkedIn — headline (2 opções) e About

Limite prático de headline: ~220 caracteres. Não usar o título “Senior Data Engineer” como se já fosse o cargo atual.

**Headline A (recomendada, prova + domínio):**
Senior Software Engineer & Tech Lead building data platforms | Python, dbt, Airflow, AWS | Payments & PIX

**Headline B (ênfase em tenure, expansão explícita):**
Backend Tech Lead → data platforms (Python, FastAPI, dbt, Airflow, Terraform) | 10+ years shipping production systems | Fintech & payments

**About (inglês, audiência internacional)**

I’m a senior software engineer and tech lead with 10+ years building production systems — mostly Python (FastAPI, Django) and Node — and I care about the unglamorous parts: clear contracts, ownership, reliable deploys, and infrastructure as code.

I’m now applying that same bar to data platforms. I designed and built an end-to-end portfolio around public PIX payments data from Banco Central do Brasil: incremental ingestion into S3, dimensional models and tests in dbt, Airflow for orchestration, Metabase for the business questions, and AWS infra in Terraform. It is a system you can clone and run.

I work best in remote, high-ownership teams. I’m particularly interested in Senior Data Engineer roles where payments, fintech, or operational analytics matter, and where a hiring manager would rather read a repo than a buzzword list.

Open to remote contracts and full-time roles (Brazil-based companies and international teams). Happy to walk through architecture trade-offs in English or Portuguese.

**About (opcional, rede brasileira)**

Sou engenheiro de software sênior e tech lead, com mais de 10 anos entregando sistemas em produção — principalmente Python (FastAPI, Django) e Node — com foco no que sustenta o sistema no dia a dia: contratos claros, ownership, deploys confiáveis e infra como código.

Estou aplicando o mesmo critério a plataformas de dados. Desenhei e construí um portfólio ponta a ponta com dados públicos do PIX (Banco Central): ingestão incremental em S3, modelos dimensionais e testes em dbt, orquestração em Airflow, dashboards no Metabase e infra AWS em Terraform. É um sistema que dá para clonar e rodar.

Busco vagas remotas de Data Engineer Sênior, com especial interesse em pagamentos, fintech e analytics operacional. Aberto a PJ no Brasil e a contratos/times internacionais. Posso conversar em português ou inglês.

## 4. Como usar este kit (e o que não fazer)

1. Esperar a tag de cada fatia (CI verde) antes de postar o LinkedIn correspondente.
2. Preencher os placeholders de métrica com números medidos; apagar a frase se o número não existir.
3. Ajustar paths conforme a estrutura do repo evoluir.
4. Nada de candidatura, post ou envio sem ok explícito — este arquivo é só o texto-fonte.
