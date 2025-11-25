# NeuralNexus Model Specification: Nexus-Goliath-v4

## 1. Overview
The **Nexus-Goliath-v4** is the flagship large language model (LLM) in the NeuralNexus portfolio, architected as a sparse Mixture-of-Experts (MoE) transformer. It is designed for high-complexity reasoning, code synthesis, and long-context document analysis. Unlike dense models, Goliath-v4 activates only a subset of its parameters per token, optimizing inference throughput without sacrificing model capacity.

This model is strictly deployed on **Cluster-Onyx** (see `cluster_onyx_specs.md`) due to its high VRAM requirements and inter-node bandwidth dependencies.

## 2. Technical Architecture
* **Total Parameters:** 500 Billion (500B).
* **Active Parameters:** 84 Billion per forward pass.
* **Architecture Type:** Decoder-only Transformer with MoE routing.
* **Expert Count:** 128 experts total.
* **Routing Strategy:** Top-2 gating with load balancing auxiliary loss.
* **Attention Mechanism:** Grouped Query Attention (GQA) with a group size of 8 to reduce KV cache memory footprint.

### 2.1 Context Window & Positional Embeddings
The model utilizes Rotary Positional Embeddings (RoPE) scaled to support a context window of **1,048,576 tokens (1M context)**. 

$$
RoPE(x, m) = x \cdot e^{im\theta}
$$

The effective context utilization has been verified up to 99.8% recall at 1M tokens via the "Needle in a Haystack" benchmark.

## 3. Training Infrastructure Dependency
Training and fine-tuning operations for Goliath-v4 are physically bound to the hardware topology described in `cluster_onyx_specs.md`.
* **Checkpoint Size:** 1.8 Terabytes (BF16).
* **Training Tokens:** 15 Trillion tokens.
* **Optimizer:** AdamW with $\beta_1=0.9, \beta_2=0.95$.

## 4. Inference & Latency
While Goliath-v4 offers superior reasoning, it incurs higher latency compared to the distilled `nexus_flash_lite.md`.
* **Time to First Token (TTFT):** ~450ms (cold start).
* **Generation Speed:** 35 tokens/second (aggregated across 8 GPUs).
* **Batch Size:** Optimized for variable batch sizes up to 256 concurrent streams.

## 5. Pricing & Commercialization
Pricing is structured based on token throughput. Note that due to the computational cost of the **Cluster-Onyx** infrastructure, this is our premium tier.

| Metric | Price (USD) |
| :--- | :--- |
| Input Tokens | $10.00 per 1,000,000 tokens |
| Output Tokens | $30.00 per 1,000,000 tokens |
| Fine-tuning | $0.005 per 1k tokens (plus fixed infrastructure fee) |

## 6. Integration Notes
* **Orion Project:** This model is the reasoning core for `project_orion_roadmap.md`.
* **Vector Database:** For RAG implementations, Goliath-v4 must be paired with `vectordb_shard_x.md` to retrieve relevant context chunks.
* **Error Handling:** If the model exceeds thermal limits on the GPU nodes, the API will return `ERR_503_MODEL_OVERLOAD` (see `api_error_codes.md`).

## 7. Known Limitations
* **Hallucination Rate:** 2.4% on zero-shot factual queries.
* **Multimodality:** Currently text-only.
* **Bias:** Shows a slight bias towards Pythonic syntax in pseudocode generation tasks.