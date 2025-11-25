# NeuralNexus Documentation: API Error Codes

## 1. Standard HTTP Codes
These codes are returned by the `edge_gateway_v2.md` standard ingress.

* **200 OK:** Request processed successfully.
* **400 Bad Request:** Malformed JSON or invalid parameters.
* **401 Unauthorized:** Invalid API Key (or token from `legacy_auth_service.md` is expired).
* **429 Too Many Requests:** You have exceeded the 5000 RPM limit.

## 2. Proprietary NeuralNexus Error Codes

### ERR_503_MODEL_OVERLOAD
* **Description:** The inference cluster is thermally throttled or at maximum capacity.
* **Trigger:** Occurs when `cluster_onyx_specs.md` sensors report coolant temp > 45°C.
* **Retry Strategy:** Exponential backoff (wait at least 30 seconds).

### ERR_400_CONTEXT_OVERFLOW
* **Description:** Input token count exceeds model window.
* **Limits:**
    * Nexus-Flash-Lite: > 32k tokens.
    * Nexus-Goliath-v4: > 1M tokens.

### ERR_500_VECTOR_SHARD_TIMEOUT
* **Description:** The vector database failed to return results within the timeout window.
* **Cause:** Usually high memory pressure on `vectordb_shard_x.md`.

## 3. Debugging
When contacting support, please include the `X-Request-ID` header from the response. Reference the `incident_response_playbook.md` if you are an internal engineer seeing these errors in production.