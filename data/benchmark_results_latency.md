# NeuralNexus Report: Latency & Throughput Benchmarks

## 1. Test Environment
* **Date:** November 20, 2024
* **Hardware:** Standard node configurations from `cluster_onyx_specs.md`.
* **Load Generator:** Locust (500 concurrent users).

## 2. Model Comparison
This table compares the heavy-duty **Nexus-Goliath-v4** against the edge-optimized **Nexus-Flash-Lite**.

| Metric | Nexus-Goliath-v4 (`nexus_goliath_v4.md`) | Nexus-Flash-Lite (`nexus_flash_lite.md`) |
| :--- | :--- | :--- |
| **Parameter Count** | 500 Billion (MoE) | 7 Billion (Dense) |
| **Time to First Token (TTFT)** | 450 ms | 12 ms |
| **Tokens Per Second (TPS)** | 35 tokens/s | 145 tokens/s |
| **Max Concurrent Streams** | 256 | 2,048 |
| **VRAM Usage per Stream** | 8 GB | 0.1 GB |

## 3. Analysis
* **Goliath-v4:** Latency is high due to the MoE routing overhead and the physical distance of memory fetches in the H100 cluster. It is unsuitable for real-time chat without streaming.
* **Flash-Lite:** The 12ms TTFT makes it ideal for voice-assistant applications routed through `edge_gateway_v2.md`.

## 4. Impact on Project Orion
Current benchmarks indicate that `project_orion_roadmap.md` will suffer from "sluggish" feel if it relies solely on Goliath-v4. A hybrid approach (routing simple queries to Flash-Lite) is recommended.