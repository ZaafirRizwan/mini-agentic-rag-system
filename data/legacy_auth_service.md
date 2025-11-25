# NeuralNexus Infrastructure: Legacy-Auth-Service [DEPRECATED]

> **WARNING:** THIS SERVICE IS END-OF-LIFE (EOL). DO NOT USE FOR NEW PROJECTS.

## 1. Status
* **Version:** v1.0.4
* **Build Date:** November 12, 2019
* **Deprecation Date:** March 15, 2024
* **Shutdown Scheduled:** December 31, 2025

## 2. Overview
The Legacy-Auth-Service provided the original identity management for NeuralNexus APIs. It utilizes a monolithic architecture backed by a PostgreSQL 10 instance. Due to security vulnerabilities exposed in the `post_mortem_march_2024.md`, this service is in strict maintenance mode.

## 3. Incompatibilities
* **Project Orion:** This service is **incompatible** with `project_orion_roadmap.md`. It cannot issue the scoped entitlements required for the Agentic workflow.
* **Edge-Gateway-v2:** The gateway (`edge_gateway_v2.md`) will stop accepting tokens from this service in the next major release.

## 4. Technical Details
* **Algorithm:** RSA-256.
* **Token Format:** Non-standard Opaque Token (Hex string).
* **Database:** `auth_db_legacy` (RDS).
* **Hardcoded Limits:** Max 500 users per organization.

## 5. Security Vulnerabilities
This service was the root cause of the data leak described in `post_mortem_march_2024.md`.
* **Flaw:** SQL Injection vulnerability in the `/verify_token` endpoint.
* **Flaw:** Weak entropy in token generation logic.
* **Remediation:** Patched in hotfix v1.0.4b, but the architecture remains fundamentally insecure.

## 6. Migration Path
Users must transition to the Hydra Identity Provider (IdP). Scripts are available in the `ops-repo` to migrate user tables.