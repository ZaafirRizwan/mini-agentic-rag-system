# NeuralNexus Model Specification: Embedding-Gecko-002

## 1. Overview
**Embedding-Gecko-002** is a high-fidelity text embedding model designed to convert unstructured text into semantic vector space. It is the foundational layer for all Retrieval Augmented Generation (RAG) workflows at NeuralNexus.

This model's outputs are strictly formatted for storage in **VectorDB-Shard-X** (see `vectordb_shard_x.md`). Incompatibility with generic vector stores may arise due to proprietary dimensionality packing.

## 2. Technical Specifications
* **Architecture:** BERT-Large based encoder with mean pooling.
* **Output Dimensionality:** 1536 dimensions.
* **Max Input Tokens:** 8,191 tokens.
* **Normalization:** L2-normalized vectors.
* **Training Objective:** Contrastive learning with Matryoshka Representation Learning (MRL) loss to allow for truncation without retraining.

$$
L_{contrastive} = - \log \frac{e^{sim(q, d^+)/\tau}}{\sum_{d \in D} e^{sim(q, d)/\tau}}
$$

## 3. Performance Metrics
* **MTEB Score:** 64.5 (Average).
* **Retrieval Accuracy:** 92% recall@10 on internal legal datasets.
* **Clustering Purity:** 0.88 on 20 newsgroups.

## 4. Integration with Project Orion
As detailed in `project_orion_roadmap.md`, Embedding-Gecko-002 is the mandatory embedding engine for the "Orion" hybrid agent. It bridges the gap between user queries and the knowledge base managed by `vectordb_shard_x.md`.

## 5. Operational Costs & Throughput
* **Latency:** ~45ms for a 512-token batch.
* **Batch Size:** Supports up to 512 simultaneous sequences.
* **Cost:** $0.0001 per 1k tokens.

## 6. Dependency Warning
Attempting to switch embedding models requires a complete re-indexing of the vector database. As noted in `vectordb_shard_x.md`, a full re-index of the 100TB dataset takes approximately 14 hours and consumes significant compute resources.

## 7. Version History
* **v001:** Deprecated. 768 dimensions.
* **v002 (Current):** 1536 dimensions. Improved multilingual support.
* **v003 (Alpha):** Variable dimension output (256-3072). Currently in testing on `cluster_onyx_specs.md` spare partitions.