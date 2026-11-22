<a href="https://www.linkedin.com/in/sammyferreira1/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/header-dark.svg">
    <img alt="Sammy Ferreira, full-stack developer" src="./assets/header-light.svg" width="100%">
  </picture>
</a>

<p align="center">
  <a href="https://www.linkedin.com/in/sammyferreira1/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-sammyferreira1-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="mailto:sammyfe2021@gmail.com"><img alt="Email" src="https://img.shields.io/badge/Email-sammyfe2021%40gmail.com-7C3AED?style=for-the-badge&logo=gmail&logoColor=white"></a>
  <img alt="Profile views" src="https://komarev.com/ghpvc/?username=SammyFerreiraa&style=for-the-badge&color=0891b2&label=PROFILE+VIEWS">
</p>

I build products that use AI and handle money, and I care about the parts that keep them correct in production: validation, queues, idempotency and tests. Most of my work lives in private client repos, so here is the short version.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/highlights-dark.svg">
  <img alt="20k+ creators, 10k+ deals a day, 1st place hackathon, 42,000x less data per query" src="./assets/highlights-light.svg" width="100%">
</picture>

## Featured work

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/project-pingo-dark.svg">
    <img alt="Pingo" src="./assets/project-pingo-light.svg" width="49%">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/project-soin-dark.svg">
    <img alt="SOIN" src="./assets/project-soin-light.svg" width="49%">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/project-creators-dark.svg">
    <img alt="Creator platform" src="./assets/project-creators-light.svg" width="49%">
  </picture>
  <a href="https://candidato.nortyra.com.br">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="./assets/project-candidato-dark.svg">
      <img alt="Candidatô" src="./assets/project-candidato-light.svg" width="49%">
    </picture>
  </a>
</p>

<details>
<summary><b>How Pingo turns a Telegram message into a WhatsApp alert</b></summary>
<br>

```mermaid
flowchart LR
    A[64 Telegram channels] -->|MTProto| B[Reader]
    B --> C[(Postgres job queue<br/>FOR UPDATE SKIP LOCKED)]
    C --> D{LLM extraction<br/>JSON Schema}
    D -->|Groq| E[Structured deal<br/>price, coupon, store]
    D -->|fallback: Together| E
    D -->|fallback: heuristics| E
    E --> F[Matcher<br/>user keyword alerts]
    F --> G[Web feed]
    F --> H[WhatsApp queue<br/>retries 1, 5, 15 min]
```

Retries are classified by error type, the queue survives WhatsApp session drops, and nothing depends on a single LLM provider.
</details>

<details>
<summary><b>How I ship with AI agents</b></summary>
<br>

- I write the spec first: inputs, outputs, edge cases and what failure looks like.
- Agents implement in small units, and each unit gets a review pass before it merges.
- Numbers that matter are computed in code, never left for the model to guess.
- Tests are the contract. On SOIN that meant about 700 of them in four days.
</details>

<details>
<summary><b>Things I like in production</b></summary>
<br>

- Postgres doing real work: job queues with `SKIP LOCKED`, advisory locks, window functions
- Money flows that survive bad days: idempotency keys, webhooks plus polling, reconciliation
- LLMs with guardrails: structured output, validation in the backend, provider fallbacks, evals
</details>

## Stack

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/stack-dark.svg">
  <img alt="TypeScript, JavaScript, React, Next.js, Node.js, NestJS, tRPC, Prisma, PostgreSQL, MySQL, Tailwind, React Native, Expo, Capacitor, Docker, Vercel, Linux, GitHub Actions, Gemini, Claude, PHP, Pix, Telegram, WhatsApp" src="./assets/stack-light.svg" width="100%">
</picture>

## Activity

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./profile/stats-dark.svg">
    <img alt="GitHub stats" src="./profile/stats-light.svg" width="49%">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./profile/top-langs-dark.svg">
    <img alt="Top languages" src="./profile/top-langs-light.svg" width="49%">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./profile/streak-dark.svg">
    <img alt="Contribution streak" src="./profile/streak-light.svg" width="60%">
  </picture>
</p>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/snake-dark.svg">
  <img alt="Snake eating my contribution graph" src="./profile/snake-light.svg" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/footer-dark.svg">
  <img alt="Thanks for stopping by" src="./assets/footer-light.svg" width="100%">
</picture>
