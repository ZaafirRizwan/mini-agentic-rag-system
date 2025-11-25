# NeuralNexus Infrastructure: Cluster-Onyx Specifications

## 1. Facility Overview
**Cluster-Onyx** is the central high-performance computing (HPC) environment for NeuralNexus. It is physically located in Data Center Zone B (Oregon). This cluster is the exclusive host for training and inference of **Nexus-Goliath-v4** (`nexus_goliath_v4.md`).

## 2. Compute Topology
* **Node Count:** 256 Nodes.
* **GPU Total:** 2,048 NVIDIA H100 Tensor Core GPUs.
* **VRAM per GPU:** 80 GB HBM3.
* **Total System VRAM:** 163,840 GB (163.8 TB).
* **Interconnect:** NVIDIA Quantum-2 InfiniBand (400Gb/s per port).

## 3. Power & Cooling
The cluster operates under extreme thermal density. 
* **Total Power Consumption:** 2.4 Megawatts (MW) at peak load.
* **Cooling Architecture:** Direct-to-Chip Liquid Cooling + Rear Door Heat Exchangers.
* **PUE (Power Usage Effectiveness):** 1.12.

### 3.1 Thermal Failure Protocols
In the event of cooling loop pressure loss or coolant temperature exceeding **45°C**:
1.  The `deployment_pipeline_ci_cd.md` is instantly locked.
2.  Active workloads are checkpointed to localized SSDs.
3.  The API Gateway returns `ERR_503_MODEL_OVERLOAD` (refer to `api_error_codes.md`).
4.  The facility shifts to "Survival Mode," throttling clock speeds by 60%.

## 4. Storage Integration
* **Hot Tier:** 2PB NVMe storage for checkpointing.
* **Throughput:** 4 TB/s aggregate read speed.
* **Dependency:** Mounts volumes from the data sanitation pipeline defined in `data_sanitization_policy.md`.

## 5. Cost Factors
Operating Cluster-Onyx is the single largest line item in the company budget.
* **Daily Energy Cost:** ~$8,500 (varies by spot pricing).
* **Maintenance Contract:** $125,000 / month.
* **Financial Impact:** See `cost_analysis_q3_2024.md` for exact Q3 operating expenses.

## 6. Deployment Constraints
Deployments to Cluster-Onyx are strictly controlled via the Blue/Green strategy outlined in `deployment_pipeline_ci_cd.md`. Unauthorized SSH access triggers immediate termination of employment.