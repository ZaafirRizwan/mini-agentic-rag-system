# NeuralNexus Model Specification: Nexus-Flash-Lite

## 1. Overview
**Nexus-Flash-Lite** is a 7-Billion parameter dense transformer model, distilled from the larger Nexus-Goliath-v4 checkpoints. It is engineered specifically for edge computing, low-latency function calling, and real-time chat applications where cost and speed are prioritized over deep reasoning capabilities.

The model is optimized for deployment via the **Edge-Gateway-v2** (see `edge_gateway_v2.md`), which handles the traffic routing and quantization on the fly.

## 2. Distillation & Architecture
* **Teacher Model:** Nexus-Goliath-v4 (Snapshot 2024-01).
* **Student Architecture:** LLaMA-style architecture with SwiGLU activations.
* **Parameter Count:** 7.2 Billion.
* **Vocabulary Size:** 128,000 tokens.
* **Quantization:** Native support for AWQ (Activation-aware Weight Quantization) and GPTQ.

### 2.1 Quantization Specs
To achieve sub-20ms latency, Flash-Lite is frequently deployed in a 4-bit quantized state.
* **Precision:** INT4 (Integer 4-bit).
* **Model Size (Quantized):** ~4.5 GB VRAM requirement.
* **Perplexity Degradation:** < 1.5% increase compared to FP16 baseline.

## 3. Performance Benchmarks
Refer to `benchmark_results_latency.md` for a direct comparison against Goliath-v4.

* **Time to First Token (TTFT):** 12ms (on A10 GPUs).
* **Throughput:** 145 tokens/second.
* **Max Context:** 32,768 tokens (32k).

## 4. Hardware & Deployment
Unlike Goliath-v4, Flash-Lite does not require the heavy `cluster_onyx_specs.md`. It is designed to run on commodity hardware or single T4/A10 instances.
* **Minimum VRAM:** 6 GB (INT4), 16 GB (FP16).
* **Container Image:** `neuralnexus/flash-lite:v2.1.0-cuda12`.

## 5. Use Cases
1.  **Classification:** Rapid intent detection for customer support bots.
2.  **Summarization:** Summarizing chat logs routed through `edge_gateway_v2.md`.
3.  **Function Calling:** Extracting JSON parameters for API requests.

## 6. Pricing
| Metric | Price (USD) |
| :--- | :--- |
| Input Tokens | $0.15 per 1,000,000 tokens |
| Output Tokens | $0.40 per 1,000,000 tokens |
| Dedicated Node | $450.00 / month |

## 7. Post-Processing & Safety
Output from Nexus-Flash-Lite passes through the standard sanitation layer. Please note that during the `post_mortem_march_2024.md` incident, it was discovered that Flash-Lite v1 lacked sufficient instruction tuning to reject SQL injection attempts. This has been rectified in v2 via the updated `data_sanitization_policy.md`.

## 8. API Configuration
To access this model, set the `model` parameter in the API payload to `nexus-flash-lite-001`.
Example Header:
`x-model-routing: edge-optimized`