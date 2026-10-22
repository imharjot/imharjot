## Harjot Singh

Full-stack engineer, backend at heart. I build systems that stay correct and fast when a lot of people hit them at the same moment.

Over the past few years, I’ve worked on backend and distributed systems—rewriting services, rethinking architectures, improving data pipelines, and making deployments more reliable. Most of that work is private, so the projects below show how I approach performance, concurrency, operations, and system design in practice.

## Selected work

- **[deployment-console](https://github.com/imharjot/deployment-console)** — a self-hosted console for teams on Amazon ECS. It reads environments, services, databases, and the connections between them straight from AWS, then adds logs, metrics, CI, guarded deploys and rollbacks, roles, an audit log, and an approval-gated API for AI agents. Next.js and TypeScript, 1,500+ tests, and a simulated AWS account so you can try it without one.
- **[lockd](https://github.com/imharjot/lockd)** — a reservation engine for unique inventory, written in Go. TTL leases, fencing tokens, fair per-key queueing, WAL recovery, and a linearizability-checked core.
- **[oversell](https://github.com/imharjot/oversell)** — a correctness fuzzer that races concurrent requests at a checkout and tells you, deterministically, whether it oversells — then hands back a replayable repro.
- **[DropHouse](https://github.com/imharjot/drophouse)** — a real-time timed-drop auction: a no-oversell bid core, a server-authoritative anti-snipe clock, and an append-only ledger you can replay.

## Open source

My recent contributions focus on correctness fixes in backend libraries and AI tooling: serialization, validation, types, and the edge cases around them.

### Merged contributions

<!-- OSS:MERGED:START -->

- **Fastify multipart** — [Multipart onFile types](https://github.com/fastify/fastify-multipart/pull/624).
- **GPT Researcher** — [Preserve loaded MCP settings](https://github.com/assafelovic/gpt-researcher/pull/2193).
- **MCO** — [Treat Ollama model names as positional probe arguments](https://github.com/mco-org/mco/pull/129).
- **Astro** — [Preserve empty request cookie values](https://github.com/withastro/astro/pull/18226).
- **Inquirer** — [Prevent submissions while a search prompt is loading](https://github.com/SBoudrias/Inquirer.js/pull/2291).
- **MCO** — [Probe the requested Ollama model directly](https://github.com/mco-org/mco/pull/128).
- **Fastify caching** — [Prevent caching non-success responses](https://github.com/fastify/fastify-caching/pull/192).
- **Fastify Postgres** — [PostgreSQL client constructor types](https://github.com/fastify/fastify-postgres/pull/219).
- **Medusa** — [Invalidate list caches when entities change](https://github.com/medusajs/medusa/pull/15747).
- **K9s** — [Clarify field-selector constraints for resource jumps](https://github.com/derailed/k9s/pull/4062).

<!-- OSS:MERGED:END -->

### Incorporated upstream

My [Instructor batch-validation fix](https://github.com/567-labs/instructor/pull/2743) was incorporated through [#2767](https://github.com/567-labs/instructor/pull/2767), with credit in the changelog. The original PR was closed without merging, so it is separate from the merged list above.

### Pending contributions

These PRs are still open. Some are awaiting review or approval for CI to run.

<!-- OSS:PENDING:START -->

<details>
<summary>View the open pull requests</summary>

| Project | Contribution |
| --- | --- |
| Axios | [Preserve nested Buffer paths in URL-encoded forms](https://github.com/axios/axios/pull/11290) |
| Chainlit | [Apply negative-feedback filters in SQLAlchemy](https://github.com/Chainlit/chainlit/pull/3069) |
| Crush | [Preserve UTF-8 when truncating fetched content](https://github.com/charmbracelet/crush/pull/4025) |
| Drizzle | [Preserve stack traces for unknown CLI errors](https://github.com/drizzle-team/drizzle-orm/pull/5910) |
| get-value | [Point package types to the built declarations](https://github.com/jonschlinkert/get-value/pull/38) |
| Hono | [Discard stale form content length during method override](https://github.com/honojs/hono/pull/5521) |
| LangChain.js | [Keep scalar OpenAI response metadata consistent across chunks](https://github.com/langchain-ai/langchainjs/pull/11084) |
| LangChain.js | [Handle Anthropic web-fetch results in streaming and serialization](https://github.com/langchain-ai/langchainjs/pull/11064) |
| LlamaIndex | [Handle empty keyword-table node IDs](https://github.com/run-llama/llama_index/pull/23360) |
| Pino | [Declare optional lastId on multistream results](https://github.com/pinojs/pino/pull/2454) |
| Pino serializers | [Serialize both branches of SuppressedError](https://github.com/pinojs/pino-std-serializers/pull/207) |
| textgen | [Fix prefix collisions in bare tool-call names](https://github.com/oobabooga/textgen/pull/7667) |

</details>

<!-- OSS:PENDING:END -->

<!-- OSS:COUNTS:START -->

*10 merged OSS PRs · 12 open. Lists refresh hourly from GitHub; personal project PRs are excluded.*

<!-- OSS:COUNTS:END -->

## Tools I reach for

- **Backend** — Go, Node.js, Fastify, TypeScript, PostgreSQL, Redis
- **Frontend** — React, Next.js, TypeScript
- **Cloud and ops** — AWS (ECS, RDS, CloudWatch), Docker, GitHub Actions
- **Also** — Java/Spring Boot, Medusa

Currently going deeper on Go and distributed-systems fundamentals.

---

## Contact

- Email — harjotsrance@gmail.com
- LinkedIn — https://www.linkedin.com/in/imharjot
- Website — https://harjotsingh.dev
