# NeuralNexus Protocols: Incident Response Playbook

## 1. Objective
This playbook defines the standard operating procedures (SOPs) for handling system outages, degradation, and security events.

## 2. Severity Levels
| Level | Description | SLA Response Time |
| :--- | :--- | :--- |
| **Sev1** | Critical Outage (API Down, Data Leak) | 15 Minutes |
| **Sev2** | Major Feature Broken (e.g., Streaming fails) | 1 Hour |
| **Sev3** | Minor Bug / Internal Tooling Down | 24 Hours |

## 3. Roles & Responsibilities
* **Incident Commander (IC):** Managing the overall response.
* **Ops Lead:** Hands-on fix implementation.
* **Comms Lead:** Updates status page and stakeholders.

## 4. Common Failure Scenarios

### 4.1 Edge-Gateway-v2 Failure
The `edge_gateway_v2.md` is the most common point of traffic congestion.
* **Symptom:** 502 Bad Gateway errors.
* **Action:** Execute `kubectl rollout restart deployment edge-gateway`.
* **Verification:** Check /healthz endpoint.

### 4.2 Cluster-Onyx Overheating
* **Symptom:** `ERR_503_MODEL_OVERLOAD` spikes (see `api_error_codes.md`).
* **Action:** Contact Data Center Ops immediately. Verify liquid cooling pump telemetry.
* **Reference:** See cooling protocols in `cluster_onyx_specs.md`.

### 4.3 VectorDB Latency Spike
* **Symptom:** Search takes > 200ms.
* **Action:** Check `vectordb_shard_x.md` memory usage. If >95%, add read replicas via Terraform.

## 5. Post-Incident
Every Sev1/Sev2 requires a written Post-Mortem within 48 hours. See `post_mortem_march_2024.md` for an example of a compliant report format.