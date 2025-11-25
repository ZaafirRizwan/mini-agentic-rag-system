# NeuralNexus Protocols: CI/CD Deployment Pipeline

## 1. Philosophy
Our deployment pipeline focuses on immutability and progressive delivery. We utilize a GitOps workflow where the state of the infrastructure is defined in version control.

## 2. Pipeline Stages
1.  **Commit:** Developer pushes code to GitLab.
2.  **Test:** Unit tests and integration tests run (blocking).
3.  **Build:** Docker containers are built and scanned for CVEs.
4.  **Deploy (Staging):** Automatic deployment to staging K8s cluster.
5.  **Deploy (Production):** Manual approval required.

## 3. Deploying to Cluster-Onyx
Deploying changes to the inference engines on **Cluster-Onyx** (`cluster_onyx_specs.md`) requires specific protocols due to the high cost of downtime.

* **Strategy:** Blue/Green Deployment.
* **The "Blue" Env:** Current live version (taking 100% traffic).
* **The "Green" Env:** New version (taking 0% traffic).
* **Switch:** Traffic is shifted 1% -> 10% -> 50% -> 100% over a 15-minute window.
* **Approvals:** Requires digital signatures from **3 Senior Engineers**.

## 4. Tools & Technologies
* **Orchestration:** Kubernetes (EKS).
* **CD Tool:** ArgoCD.
* **CI Tool:** GitLab CI.
* **Registry:** Harbor.

## 5. Rollback Procedures
If the error rate defined in `api_error_codes.md` exceeds 0.5% during rollout:
1.  ArgoCD automatically triggers a rollback to the previous revision.
2.  Alerts are sent to the #ops-critical Slack channel.
3.  The "Green" environment is preserved for forensic analysis.

## 6. Relationship to Edge-Gateway
Configuration changes to `edge_gateway_v2.md` are deployed separately from model updates to prevent simultaneous failures in routing and inference layers.