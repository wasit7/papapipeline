# **Chapter 7: Ingest & Clean Flow Design**

> **Goal for the final project**
> Build a **daily ETL pipeline** that ingests raw data, cleans it, version-controls every artefact **in lakeFS**, and makes the output ready for EDA and ML.
> This chapter shows how to turn that idea into a single **Prefect 3 flow** that can be deployed, retried, audited, and rolled back.

---

## **7.0 Big-Picture Architecture**

```
 ┌────────────┐     ┌─────────┐     ┌──────────────┐
 │  Raw Source│ --> │ Prefect │ --> │ lakeFS Repo  │
 └────────────┘     │  Worker │     │              │
                    └─────────┘     └────────┬─────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Downstream    │
                                    │  EDA / ML Flow  │
                                    └─────────────────┘
```

* **Prefect Server/UI** orchestrates the workflow.
* **Prefect Worker** runs inside Docker (tutorial 07’s `prefect-worker` service).
* **lakeFS** (backed by MinIO) stores **every version** of raw and cleaned data.

  * Branch naming convention: `etl/{execution_date}`.
  * Commits are atomic; merges promote data to `main`.

---

## **7.1 Flow Parameters & Work-Pool Wiring**

| Parameter        | Type                              | Purpose                                             |
| ---------------- | --------------------------------- | --------------------------------------------------- |
| `execution_date` | `str` (`YYYY-MM-DD`)              | Determines source URL/path; unique branch in lakeFS |
| `run_type`       | `str` (`"backfill"` \| `"daily"`) | Adjusts concurrency, retries                        |
| `bucket`         | `str` (default `"lakefs"`)        | S3-style bucket where lakeFS listens                |

```python
from prefect import flow, task, get_run_logger
from datetime import date

@flow(name="ingest-clean",
      retries=0,         # top-level retries disabled; leave to individual tasks
      log_prints=True)
def ingest_clean_flow(
    execution_date: str = date.today().isoformat(),
    run_type: str = "daily",
    bucket: str = "lakefs",
):
    ...
```

*Deploy the flow to a **work pool** “etl-pool” so workers with higher memory handle Parquet writes.*

---

## **7.2 Extract Task (pull raw data)**

```python
import httpx
from pathlib import Path

@task(retries=3, retry_delay_seconds=30)
def extract_raw(execution_date: str) -> Path:
    url = f"https://api.example.com/events?date={execution_date}"
    local = Path(f"/tmp/raw_{execution_date}.json")
    r = httpx.get(url, timeout=30.0)
    r.raise_for_status()
    local.write_bytes(r.content)
    get_run_logger().info(f"Downloaded {local.stat().st_size/1024:.1f} KB")
    return local
```

*Three retries + 30 s back-off satisfy **resiliency** requirement.*

---

## **7.3 Commit Raw to a lakeFS Branch**

### 7.3.1 Quick refresher on lakeFS

* Think “**Git for data**”.
* S3 API compatible → can use any S3 client (`boto3`, `s3fs`).
* **Branch → Commit → Merge** cycle just like Git.

### 7.3.2 Helper: `lakefs_client.BlockingClient`

```python
import os, boto3, uuid

LAKEFS_ENDPOINT   = os.environ["LAKEFS_ENDPOINT"]        # http://lakefs:8000
LAKEFS_ACCESS_KEY = os.environ["LAKEFS_ACCESS_KEY"]
LAKEFS_SECRET_KEY = os.environ["LAKEFS_SECRET_KEY"]

def lakefs_s3():
    return boto3.client(
        "s3",
        endpoint_url=LAKEFS_ENDPOINT,
        aws_access_key_id=LAKEFS_ACCESS_KEY,
        aws_secret_access_key=LAKEFS_SECRET_KEY,
    )
```

### 7.3.3 Task: `commit_raw_to_lakefs`

```python
@task
def commit_raw_to_lakefs(local_path: Path, branch: str, repo: str = "project"):
    s3 = lakefs_s3()
    key = f"{branch}/raw/{local_path.name}"
    s3.upload_file(Filename=str(local_path), Bucket=repo, Key=key)
    # Make a lightweight commit via lakeFS REST
    import requests, json
    _ = requests.post(
        f"{LAKEFS_ENDPOINT}/api/v1/repositories/{repo}/branches/{branch}/commits",
        auth=(LAKEFS_ACCESS_KEY, LAKEFS_SECRET_KEY),
        json={"message": f"Raw ingest {local_path.name}"},
    )
    return f"s3://{repo}/{key}"
```

*Branch is created implicitly by the first commit (tutorial 07 default behaviour).*

---

## **7.4 Transform (Clean) Task**

Cleaning rules replicate **Chapter 6**:

```python
import pandas as pd

@task
def clean_dataset(raw_uri: str) -> pd.DataFrame:
    df = pd.read_json(raw_uri, storage_options={"client": lakefs_s3()})
    # --- Rename to snake_case
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    # --- Cast types
    df["price"] = (
        df["price"].astype(str)
        .str.replace(",", "")
        .astype("float64")
    )
    # --- Convert timestamp to UTC
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    # --- Drop duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["event_id"])
    get_run_logger().info(f"Dropped {before - len(df)} duplicate rows")
    return df
```

---

## **7.5 Load Task (write cleaned Parquet)**

```python
@task
def load_parquet(df: pd.DataFrame, branch: str, repo: str = "project") -> str:
    key = f"{branch}/curated/events.parquet"
    uri = f"s3://{repo}/{key}"
    df.to_parquet(
        uri,
        engine="pyarrow",
        compression="snappy",
        storage_options={"client": lakefs_s3()},
    )
    # Commit again
    import requests
    _ = requests.post(
        f"{LAKEFS_ENDPOINT}/api/v1/repositories/{repo}/branches/{branch}/commits",
        auth=(LAKEFS_ACCESS_KEY, LAKEFS_SECRET_KEY),
        json={"message": "Cleaned Parquet"},
    )
    return uri
```

---

## **7.6 Merge-to-Main (idempotent promotion)**

```python
@task
def merge_to_main(branch: str, repo: str = "project"):
    import requests
    resp = requests.post(
        f"{LAKEFS_ENDPOINT}/api/v1/repositories/{repo}/refs/{branch}/merge",
        auth=(LAKEFS_ACCESS_KEY, LAKEFS_SECRET_KEY),
        json={"destination_branch": "main", "message": f"Promote {branch}"},
    )
    resp.raise_for_status()
```

*If the same execution date runs twice, lakeFS will detect identical object hashes → merge remains idempotent.*

---

## **7.7 Putting It Together**

```python
@flow(name="ingest-clean", log_prints=True)
def ingest_clean_flow(
    execution_date: str = date.today().isoformat(),
    run_type: str = "daily",
    bucket: str = "lakefs",
    repo: str = "project",
):
    branch = f"etl/{execution_date}"

    raw_local  = extract_raw(execution_date)
    raw_uri    = commit_raw_to_lakefs(raw_local, branch, repo)
    df_clean   = clean_dataset(raw_uri)
    parquet_uri= load_parquet(df_clean, branch, repo)
    merge_to_main(branch, repo)              # promotes curated data
    get_run_logger().info(f"✅ Ready at {parquet_uri}")
```

### CLI Deployment

```bash
prefect deployment build ingest_clean.py:ingest_clean_flow \
    --name daily-ingest \
    --work-pool etl-pool \
    --schedule "0 3 * * *" \
    --apply
```

*Runs at 03:00 every day; each run makes its own branch `etl/2025-05-20`, commits, and merges.*

---

## **7.8 Secrets Management**

Add a **Prefect Secret Block** named `lakefs-creds` via UI or CLI:

```bash
prefect block register -m prefect.blocks.system
prefect block create --type secret --name lakefs-creds
# Paste access + secret key as JSON
```

In code:

```python
from prefect.blocks.system import Secret
LAKEFS_ACCESS_KEY, LAKEFS_SECRET_KEY = (
    Secret.load("lakefs-creds").get().split(":")
)
```

---

## **7.9 Idempotency Checklist**

1. **Branch per `execution_date`** – second run commits identical hashes, merge is no-op.
2. **Upsert not append** – Parquet rewrite replaces file.
3. **Deterministic file names** – avoid UUIDs in output paths.
4. **Retries only on *extract*** – transformation tasks are pure functions; safe to rerun.

---

## **7.10 Summary**

By:

* **Branching every run** you create isolated, immutable snapshots of raw and cleaned data.
* **Committing** within tasks you tie data lineage to Prefect run-ids automatically.
* **Merging to `main`** only after validation you guarantee that curated data in `main` always meets the Chapter 6 rubric.

You now own a production-ready **Ingest + Clean** pipeline ready for Chapter 8’s EDA tasks and Chapter 9’s ML baseline.
