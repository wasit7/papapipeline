# **Chapter 6: Data-Quality Engineering**

Data quality is the first—and most frequently underestimated—pillar of every analytic or ML workflow.  In the **final project**, 50 % of the technical score comes directly from measurable quality targets:

* ≥ 90 % completeness for every column
* 0 duplicate rows
* No columns stored as the generic `object` dtype
* Explicit schema that never drifts

This chapter shows how to reach those targets *and* automate the evidence trail inside Prefect.

---

## **6.1 Why Data Quality Matters**

> “Garbage in, garbage out” is amplified when you automate garbage at scale.

Poor-quality data causes silent model drift, orchestration failures, and wasted compute.  Prefect’s orchestration layer can turn quality checks into **first-class tasks** that fail fast, keeping dirty data from contaminating downstream steps.

---

## **6.2 Core Quality Dimensions**

| Dimension        | Operational definition                             | Project rubric link          |
| ---------------- | -------------------------------------------------- | ---------------------------- |
| **Completeness** | % of non-null cells                                | ≥ 90 % per column            |
| **Validity**     | Values meet format or domain rules (regex, ranges) | Schema file & Pandera checks |
| **Uniqueness**   | No duplicate primary-key rows                      | 0 duplicates                 |
| **Consistency**  | Related fields agree (`created_at` ≤ `updated_at`) | Temporal logic task          |
| **Timeliness**   | Data arrive within SLA (24 h coverage)             | “Data-clock” plot in Chap 8  |

---

## **6.3 Profiling & Metrics**

### 6.3.1 Quick profiling with `pandas_profiling`

```python
import pandas as pd
from ydata_profiling import ProfileReport  # new name of pandas_profiling

df = pd.read_parquet("raw/events.parquet")
profile = ProfileReport(df, title="Events profile")
profile.to_file("reports/profile.html")
```

> **Tip:** Run this once per new data source; afterwards codify rules in Pandera or Great Expectations.

### 6.3.2 Pandera schema in pure Python

```python
import pandera as pa
from pandera import Column, Check

EventSchema = pa.DataFrameSchema(
    {
        "event_id"   : Column(pa.Int, unique=True),
        "timestamp"  : Column(pa.DateTime),
        "price"      : Column(pa.Float, Check.gt(0)),
        "province_id": Column(pa.Int, Check.isin(range(1, 78))),
    }
)
```

Running `EventSchema.validate(df)` returns a clean DataFrame **or** raises `SchemaError`, which Prefect can catch.

### 6.3.3 YAML-based schema (declarative)

```yaml
# dataset-schema.yaml
columns:
  event_id   : {dtype: int64, unique: true}
  timestamp  : {dtype: datetime64[ns]}
  price      : {dtype: float64, gt: 0}
  province_id: {dtype: int64, isin: [1-77]}
```

Storing this file in Git makes the contract version-controlled (“schema-as-code”).

---

## **6.4 Validation Tasks inside Prefect**

```python
from prefect import flow, task, get_run_logger
import pandas as pd
from pandera import errors

@task(retries=3, retry_delay_seconds=10)
def load_raw(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)

@task
def validate(df: pd.DataFrame) -> pd.DataFrame:
    from schema import EventSchema  # python schema above
    try:
        return EventSchema.validate(df)
    except errors.SchemaError as err:
        # Mark the task—and therefore the flow—as FAILED
        raise RuntimeError(f"Validation failed: {err}")  # Prefect captures this
```

The retry pattern is identical to the one you used in earlier flows .

### 6.4.1 Calculating and logging completeness

```python
@task
def calc_completeness(df: pd.DataFrame) -> dict:
    completeness = 1 - df.isna().mean()
    get_run_logger().info({"completeness": completeness.to_dict()})
    return completeness.to_dict()
```

Because `log_prints=True` or explicit `get_run_logger()` is used, the metric appears in the Prefect UI logs .

### 6.4.2 Raising a flow-level FAIL if targets missed

```python
@flow(log_prints=True)
def quality_flow(src: str):
    df   = load_raw(src)
    _    = validate(df)
    mets = calc_completeness(df)
    if min(mets.values()) < 0.90:
        raise ValueError("Completeness below 90 %!")

if __name__ == "__main__":
    quality_flow.serve(name="daily-quality-check", work_pool_name="dev-pool")
```

---

## **6.5 Trend Dashboards**

* Use **Prefect Artifacts** to attach a tiny CSV of metrics to each run.
* In a separate BI tool (Metabase, Superset) or a quick Jupyter notebook, plot the metric over time and add a red threshold line at 0.90.
* A single glance tells whether your data supply is degrading.

```python
from prefect.artifacts import create_table_artifact
import pandas as pd, datetime as dt

@task
def save_artifact(metrics: dict):
    df = pd.DataFrame([metrics])
    create_table_artifact(
        key="quality-metrics",
        table=df,
        description=f"Metrics on {dt.date.today()}",
    )
```

Artifacts show up per run **and** aggregate under *Artifacts* in the Prefect UI.

---

## **6.6 Best-Practice Checklist**

1. **Define once, enforce always** – keep `dataset-schema.yaml` next to your code.
2. **Fail fast** – run validation before heavy transforms.
3. **Treat metrics as logs** – push completeness/duplicate\_rate so they live in Prefect’s history.
4. **Normalise time** – store all timestamps in UTC to avoid daylight-saving bugs.
5. **Avoid `object` dtype** – always cast numerics; Pandera can enforce.
6. **Automate duplicates check** – use `df.duplicated().any()` inside a task.
7. **Document exceptions** – if 100 % completeness is impossible (e.g., optional field), record rationale in README.

---

## **6.7 Summary**

By integrating profiling tools (**pandera**, **ydata-profiling**) and fail-fast validation tasks directly into Prefect flows you:

* Guarantee that only clean, well-typed data enters downstream analytics.
* Produce an auditable history of quality metrics.
* Meet the rubric’s stringent targets long before the final presentation.

Next, you will build on this foundation in **Chapter 7**, converting validation logic into a reproducible `extract → transform → load` pipeline that ingests fresh data daily.
