# Learning Notes — Phase 0: Scaffolding, Configuration, and dlt Contracts

---

## 1. Concepts Introduced in Phase 0

### Modern Data Lakehouse Ingestion: ELT vs. Legacy ETL
- **What it is:** In legacy **ETL** (Extract-Transform-Load), data was heavily transformed in memory or on intermediate servers before landing in rigid relational databases. In a modern **ELT Lakehouse** (Extract-Load-Transform), raw data is extracted from APIs, quickly persisted into immutable object storage (like MinIO / S3) as compressed columnar files (**Parquet**), and loaded into an analytical columnar database (**ClickHouse**) where transformations are performed via SQL views.
- **Why it matters:** ELT preserves raw data lineage. If transformation logic changes or a downstream schema evolves, you do not need to re-query the third-party upstream API (which is slow, rate-limited, and expensive); you simply replay the data already residing in your object storage.

### Embedded Ingestion Engines: Why `dlt`?
- **What it is:** `dlt` (data load tool) is a lightweight, Python-first ingestion library that turns Python generators into production-grade data pipelines.
- **Why not Airflow or Spark here?** Heavy distributed frameworks (Spark, Kafka, Airflow) introduce massive infrastructure overhead (JVMs, ZooKeeper/Raft clusters, worker nodes). For CRM ingestion handling millions of records, a single Python process utilizing streaming generators, micro-batch chunking, and worker threads is faster, radically simpler to maintain, and can run anywhere (laptop, container, or cloud function).

### Filesystem Destination & S3 Storage Abstraction
- **What it is:** `dlt.destinations.filesystem` abstracts storage through protocols (`file://`, `s3://`, `gcs://`, `az://`). 
- **Under the hood:** It uses `fsspec` and `s3fs` / `aiobotocore` to interface with S3-compatible endpoints like **MinIO**. When writing to `s3://hubspot-lake`, the pipeline issues standard AWS S3 API commands (`PutObject`, `ListObjectsV2`) indistinguishable from AWS S3.

### Columnar Storage & Parquet Compression
- **What it is:** Unlike row-oriented formats (CSV, JSONL) where data is stored record by record, **Apache Parquet** stores data column by column.
- **Why it matters for analytics:**
  1. **Projection pruning:** Queries asking for `sum(amount)` read only the `amount` column from disk, skipping all other columns entirely.
  2. **High compression ratios:** Similar data types placed together compress significantly better. Using `zstd` (Zstandard) or `snappy`, Parquet files are typically 70% to 90% smaller than raw JSON.
  3. **Embedded metadata & statistics:** Parquet files store min/max values and dictionary encodings inside file footers, allowing readers to skip whole chunks of data without scanning.

### Incremental Loading, High Watermarks, and Boundary Ties
- **What it is:** An incremental pipeline only extracts records that have been created or modified since the previous sync. The cursor value (e.g. `updated_at`) representing the progress is called the **high watermark**.
- **The Boundary Tie Problem:** What if 5 records have the *exact same* millisecond timestamp `2026-03-01T12:00:00.000Z`, and 3 fit on page 1 while 2 overflow onto page 2? If you query with `updated_at > last_value`, you miss the 2 ties! If you query with `updated_at >= last_value`, you re-fetch the 3 already ingested ties!
- **How dlt solves this:** `dlt.sources.incremental(row_order="asc", primary_key="id")` queries using `>= last_value` and maintains a set of boundary hashes (`unique_hashes`) in pipeline state. On subsequent syncs, it filters out records that match the hashes of records already committed at that exact cursor boundary.

### Cross-Platform Gotchas: Windows MAX_PATH (260 Characters)
- **What we caught:** On Windows, the legacy Win32 API imposes a default 260-character maximum path length (`MAX_PATH`). During pytest execution with temporary directories (`AppData/Local/Temp/pytest-of-user/...`), long generated pipeline and dataset names pushed a state file path to 267 characters, causing `FileNotFoundError [Errno 2]`.
- **The fix:** Always keep dataset and pipeline identifiers concise and parameterized to remain well within filesystem boundaries across all host platforms (Linux, macOS, Windows).

---

## 2. Real Verification Output

### Command 1: Pytest Suite Execution
```text
$ .\.venv\Scripts\pytest.exe -v tests/unit/test_phase0_scaffold.py

============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\pangu\OneDrive\Desktop\hubspot-lakehouse-pipeline\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\pangu\OneDrive\Desktop\hubspot-lakehouse-pipeline
plugins: anyio-4.15.1, Faker-40.43.0
collecting ... collected 4 items

tests/unit/test_phase0_scaffold.py::test_settings_default_values PASSED  [ 25%]
tests/unit/test_phase0_scaffold.py::test_settings_singleton PASSED       [ 50%]
tests/unit/test_phase0_scaffold.py::test_cli_config_command PASSED       [ 75%]
tests/unit/test_phase0_scaffold.py::test_dlt_filesystem_and_incremental_contracts PASSED [100%]

============================== 4 passed in 1.57s ==============================
```

### Command 2: CLI Configuration Display
```text
$ .\.venv\Scripts\python.exe -m hubspot_pipeline.cli config

                  Pipeline Configuration                   
+---------------------------------------------------------+
| Setting                     | Value                     |
|-----------------------------+---------------------------|
| hubspot_api_base_url        | http://localhost:8080     |
| hubspot_api_token           | mock-dev-token-secret-123 |
| hubspot_timeout_seconds     | 30.0                      |
| minio_endpoint_url          | http://localhost:9000     |
| minio_internal_endpoint_url | http://minio:9000         |
| minio_access_key            | minioadmin                |
| minio_secret_key            | minioadmin                |
| minio_bucket                | hubspot-lake              |
| minio_region                | us-east-1                 |
| clickhouse_host             | localhost                 |
| clickhouse_http_port        | 8123                      |
| clickhouse_native_port      | 9100                      |
| clickhouse_user             | default                   |
| clickhouse_password         |                           |
| clickhouse_database         | hubspot                   |
| control_db_path             | state\control.db          |
| dlt_pipelines_dir           | state\dlt                 |
| pipeline_chunk_pages        | 20                        |
| max_parallel_workers        | 4                         |
| heartbeat_timeout_seconds   | 60.0                      |
| s3_bucket_url (derived)     | s3://hubspot-lake         |
+---------------------------------------------------------+
```

---

## 3. Interview-Style Q&A

### Question
> *"When building an incremental data pipeline from an upstream REST API that updates records in place, how do you prevent data loss and duplicates if the API only exposes an `updated_at` timestamp where multiple records can share the identical millisecond timestamp?"*

### Answer
> *"This is the classic **timestamp tie-breaker / cursor boundary problem** in data engineering.*
>
> *If an ingestion pipeline uses strict inequality (`updated_at > last_checkpoint`), any records sharing the same timestamp that were not returned in the prior sync (e.g. split across API page boundaries) will be permanently skipped and lost.*
>
> *If the pipeline instead uses non-strict inequality (`updated_at >= last_checkpoint`), records with that exact boundary timestamp will be re-fetched on the next run, causing duplicates.*
>
> *To solve this cleanly:*
> 1. *At the **Extraction layer**, we configure the pipeline to query with `>= last_checkpoint` sorted ascending (`ORDER BY updated_at ASC, id ASC`). The extraction framework (such as `dlt`) tracks not just the high-watermark timestamp, but also a set of cryptographic hashes representing the primary keys of records committed at that boundary (`unique_hashes`). When the next sync runs, it filters out already-seen records at that exact boundary timestamp.*
> 2. *At the **Storage/Warehouse layer**, we never rely on the extraction layer alone for correctness. In distributed systems, crashes mid-chunk can cause re-extraction. We ensure **idempotency at the sink** by writing to an analytical engine that deduplicates by primary key — in our case, ClickHouse's `ReplacingMergeTree(updated_at)` ordered by `id`.*
> 
> *Together, this delivers **at-least-once extraction with an idempotent sink**, guaranteeing effectively-once analytical results with zero data loss."*
