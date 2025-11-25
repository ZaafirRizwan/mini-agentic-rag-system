# NeuralNexus Confidential: Project Orion Roadmap

## 1. Vision
**Project Orion** is the next-generation "Agentic AI" platform. It moves beyond simple text generation to autonomous task execution. It combines the reasoning power of **Nexus-Goliath-v4** (`nexus_goliath_v4.md`) with the long-term memory of **Embedding-Gecko-002** (`embedding_gecko_002.md`).

## 2. Architecture
Orion operates as a recursive loop:
1.  **Perceive:** Input processed by `nexus_goliath_v4.md`.
2.  **Recall:** Context retrieved from `vectordb_shard_x.md`.
3.  **Act:** Tools executed via `edge_gateway_v2.md` function calling.

## 3. Development Phases

### Phase 1: Alpha (Current)
* **Goal:** Internal demo of "Talk to your Database".
* **Budget:** $2,000,000.
* **Status:** Blocked by `legacy_auth_service.md` incompatibility. We are waiting for the new IDP rollout.

### Phase 2: Beta (Q4 2024)
* **Goal:** Public release to select Enterprise partners.
* **Requirement:** Must achieve < 1 second latency. This is currently failing (see `benchmark_results_latency.md`).

## 4. Dependencies
* **Hardware:** Requires 25% of `cluster_onyx_specs.md` capacity dedicated to agent reasoning loops.
* **Security:** Strictly governed by `data_sanitization_policy.md` to prevent agents from leaking data.