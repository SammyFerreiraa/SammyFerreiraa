<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/bento-dark.svg">
  <img alt="Sammy Ferreira, full-stack developer. 20k+ creators on a platform I built as sole dev, 10k+ deals parsed a day with LLMs, 1st place at the TJCE-UFC Hackathon 2026. Projects: Pingo, Candidatô, SOIN and a creator platform." src="./profile/bento-light.svg" width="100%">
</picture>

<p align="center">
  <a href="https://www.linkedin.com/in/sammyferreira1/"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-sammyferreira1-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"></a>
  <a href="mailto:sammyfe2021@gmail.com"><img alt="Email" src="https://img.shields.io/badge/Email-sammyfe2021%40gmail.com-C4532A?style=for-the-badge&logo=gmail&logoColor=white"></a>
  <img alt="Profile views" src="https://komarev.com/ghpvc/?username=SammyFerreiraa&style=for-the-badge&color=d1873b&label=PROFILE+VIEWS">
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
