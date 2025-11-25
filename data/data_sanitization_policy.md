# NeuralNexus Protocols: Data Sanitization Policy

## 1. Purpose
This policy dictates how training data and user inputs must be scrubbed of Personally Identifiable Information (PII) and malicious code before entering our systems.

## 2. Context
This policy was significantly revised following the **March 2024 Data Leak** (see `post_mortem_march_2024.md`). The previous regex-based approach was deemed insufficient.

## 3. Sanitization Layers

### 3.1 Ingestion Layer
All text entering via `edge_gateway_v2.md` passes through the "Presidio" scrubber.
* **Detected Entities:** Names, SSNs, Credit Cards, Emails, IP Addresses.
* **Action:** Replace with tokens (e.g., `<PERSON_NAME>`, `<EMAIL_ADDRESS>`).
* **Success Rate Requirement:** 99.9%.

### 3.2 Training Data (Pre-training)
Data used for training models like `nexus_goliath_v4.md` undergoes:
1.  **De-duplication:** MinHash LSH.
2.  **Toxic Content Filtering:** BERT-based classifier.
3.  **PII Redaction:** Named Entity Recognition (NER) models.

## 4. Retention Policy
* **Raw Logs:** Retained for 7 days.
* **Sanitized Logs:** Retained for 5 years.
* **Vector Embeddings:** Stored in `vectordb_shard_x.md` indefinitely unless deletion is requested.

## 5. SQL Injection Prevention
Specific to the vulnerability found in `legacy_auth_service.md`:
* All database queries must use parameterized inputs.
* String concatenation for SQL queries is strictly prohibited.
* Static Analysis tools (SonarQube) will block CI/CD pipelines (`deployment_pipeline_ci_cd.md`) if SQL flaws are detected.