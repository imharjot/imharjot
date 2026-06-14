## Harjot Singh

Full-stack engineer, backend at heart. I build commerce systems that stay correct and fast when a lot of people hit them at the same moment.

For the last few years I've worked on a B2B diamond-trading platform — real-time bidding and timed drops, inventory and order pipelines, and the concurrency control that keeps a one-of-a-kind item from being sold twice. Most of that work is private, so the projects below are where I show how I think about these problems.

## Selected work

- **[lockd](https://github.com/imharjot/lockd)** — a reservation engine for unique inventory, written in Go. TTL leases, fencing tokens, fair per-key queueing, WAL recovery, and a linearizability-checked core.
- **[oversell](https://github.com/imharjot/oversell)** — a correctness fuzzer that races concurrent requests at a checkout and tells you, deterministically, whether it oversells — then hands back a replayable repro.
- **[DropHouse](https://github.com/imharjot/drophouse)** — a real-time timed-drop auction: a no-oversell bid core, a server-authoritative anti-snipe clock, and an append-only ledger you can replay.

## Tools I reach for

Backend — Go, Node.js, Fastify, TypeScript, PostgreSQL, Redis
Frontend — React, Next.js, TypeScript
Also — Java/Spring Boot, Medusa, Docker

Currently going deeper on Go and distributed-systems fundamentals, with the occasional open-source contribution.

---

## Contact

- Email — harjotsrance@gmail.com
- LinkedIn — https://www.linkedin.com/imharjot
- Website — https://harjotsingh.dev
