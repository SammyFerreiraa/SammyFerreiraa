<p><a href="https://www.linkedin.com/in/sammyferreira1/"><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/hero-dark.svg"><img alt="Sammy Ferreira, full-stack developer from Fortaleza. Most of my code lives in private repos, so this is the trailer." src="./profile/hero-light.svg" width="100%"></picture></a></p>

<p><a href="https://www.linkedin.com/in/sammyferreira1/"><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/linkedin-dark.svg"><img alt="LinkedIn: in/sammyferreira1" src="./profile/linkedin-light.svg" width="49.7%"></picture></a><a href="mailto:sammyfe2021@gmail.com"><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/email-dark.svg"><img alt="Email: sammyfe2021@gmail.com" src="./profile/email-light.svg" width="49.7%"></picture></a></p>

<p><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/stats-dark.svg"><img alt="20k+ creators on a platform I built as sole dev, 10k+ deals parsed a day with LLMs, 1st place at the TJCE-UFC Hackathon 2026, 42,000x less data per query after a SQL rewrite" src="./profile/stats-light.svg" width="100%"></picture></p>

<p><a href="https://pingo.nortyra.com.br"><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/pingo-dark.svg"><img alt="Pingo: deal alerts on WhatsApp, pingo.nortyra.com.br" src="./profile/pingo-light.svg" width="57.6%"></picture></a><a href="https://candidato.nortyra.com.br"><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/candidato-dark.svg"><img alt="Candidatô: job application emails, candidato.nortyra.com.br" src="./profile/candidato-light.svg" width="41.9%"></picture></a></p>

<p><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/soin-dark.svg"><img alt="SOIN: case management for an environmental court, hackathon winner" src="./profile/soin-light.svg" width="57.6%"></picture><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/creators-dark.svg"><img alt="Creator platform: 20k+ creators, Pix payouts, iOS and Android" src="./profile/creators-light.svg" width="41.9%"></picture></p>

<details>
<summary><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/q0-dark.svg"><img alt="How Pingo turns a Telegram message into a WhatsApp alert" src="./profile/q0-light.svg" width="98.3%" align="middle"></picture></summary>
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
<summary><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/q1-dark.svg"><img alt="How I ship with AI agents" src="./profile/q1-light.svg" width="98.3%" align="middle"></picture></summary>
<br>

- I write the spec first: inputs, outputs, edge cases and what failure looks like.
- Agents implement in small units, and each unit gets a review pass before it merges.
- Numbers that matter are computed in code, never left for the model to guess.
- Tests are the contract. On SOIN that meant about 700 of them in four days.
</details>

<details>
<summary><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/q2-dark.svg"><img alt="Things I like in production" src="./profile/q2-light.svg" width="98.3%" align="middle"></picture></summary>
<br>

- Postgres doing real work: job queues with `SKIP LOCKED`, advisory locks, window functions
- Money flows that survive bad days: idempotency keys, webhooks plus polling, reconciliation
- LLMs with guardrails: structured output, validation in the backend, provider fallbacks, evals
</details>

<p><picture><source media="(prefers-color-scheme: dark)" srcset="./profile/bottom-dark.svg"><img alt="Stack and contribution graph, updated by a GitHub Action" src="./profile/bottom-light.svg" width="100%"></picture></p>

<p align="center"><img alt="Profile views" src="https://komarev.com/ghpvc/?username=SammyFerreiraa&style=flat-square&color=d1873b&label=profile+views"></p>
