# **Chapter 8: Exploratory Data Analysis (EDA) & Visualisation**

*Case Study – Hourly PM₂.₅ in Bangkok*

We now have a **curated Parquet** file in lakeFS (`s3://project/main/curated/pm25.parquet`) that contains hourly measurements of fine-particulate matter (PM₂.₅) plus meteorological and co-pollutant variables:

| Column      | Example                | Unit / Type  |
| ----------- | ---------------------- | ------------ |
| `timestamp` | 2025-05-19 00:00+07:00 | UTC          |
| `pm25`      | 21.4                   | µg m⁻³       |
| `temp_c`    | 29.3                   | °C           |
| `rh_pct`    | 78                     | %            |
| `wind_mps`  | 2.1                    | m s⁻¹        |
| `no2_ppb`   | 15                     | ppb          |
| `o3_ppb`    | 12                     | ppb          |
| `site_id`   | A                      | Station code |

This chapter turns those numbers into **insights** and **graphics** that:

* verify 24 h completeness (rubric link);
* reveal distribution shape and outliers;
* show how weather covariates relate to PM₂.₅;
* live as **Prefect Artifacts** so each run has a permanent, clickable EDA packet.

---

## **8.0 Learning Outcomes**

1. **Load curated Parquet from lakeFS** inside a Prefect task.
2. Produce five key plots with *pure matplotlib* (no seaborn):

   * coverage bar (“data-clock”),
   * time-series line,
   * histogram,
   * box-plot,
   * scatter + regression.
3. Publish PNGs and a summary table as Prefect **Artifacts**.
4. Embed images with **relative paths** in `README.md`.
5. Apply inclusive colour palettes & readable labels.

---

## **8.1 Loading PM₂.₅ Data**

```python
import boto3, os, pyarrow.dataset as ds, pandas as pd

LAKEFS = {
    "endpoint_url": os.getenv("LAKEFS_ENDPOINT"),
    "aws_access_key_id": os.getenv("LAKEFS_ACCESS_KEY"),
    "aws_secret_access_key": os.getenv("LAKEFS_SECRET_KEY"),
}

def load_pm25(branch: str = "main", repo: str = "project") -> pd.DataFrame:
    uri = f"s3://{repo}/{branch}/curated/pm25.parquet"
    s3  = boto3.client("s3", **LAKEFS)
    return ds.dataset(uri, filesystem=ds.S3FileSystem(client=s3))\
             .to_table().to_pandas()
```

---

## **8.2 Five Essential Plots**

All functions save a PNG in `figs/` so they can later be uploaded as artifacts.

### 8.2.1 Hourly Coverage (“Data-Clock”)

```python
import matplotlib.pyplot as plt

def plot_coverage(df, ts="timestamp", path="figs/coverage.png"):
    hours = df[ts].dt.hour.value_counts().reindex(range(24), fill_value=0)
    plt.figure(figsize=(10,3))
    plt.bar(hours.index, hours.values)
    plt.xticks(range(24)); plt.ylabel("# Observations")
    plt.title("Hourly Coverage of PM\u2082\u2009\u00B5 Dataset")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()
```

> **Interpretation** – any zero bar flags missing data (violating the 24 h rubric).

### 8.2.2 Time-Series Line

```python
def plot_timeseries(df, ts="timestamp", y="pm25",
                    path="figs/pm25_line.png"):
    plt.figure(figsize=(12,3))
    plt.plot(df[ts], df[y], linewidth=.8)
    plt.ylabel("PM\u2082\u2009\u00B5 (µg m$^{-3}$)")
    plt.title("Hourly PM\u2082\u2009\u00B5 Time-Series")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()
```

### 8.2.3 Distribution Histogram

```python
def plot_hist(df, col="pm25", path="figs/hist_pm25.png"):
    plt.figure(figsize=(5,4))
    plt.hist(df[col], bins='fd')          # Freedman-Diaconis rule
    plt.xlabel("PM\u2082\u2009\u00B5 (µg m$^{-3}$)")
    plt.ylabel("Frequency")
    plt.title("PM\u2082\u2009\u00B5 Distribution")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()
```

### 8.2.4 Box-Plot (Outliers)

```python
def plot_box(df, col="pm25", path="figs/box_pm25.png"):
    plt.figure(figsize=(3,6))
    plt.boxplot(df[col], vert=True, patch_artist=True)
    plt.ylabel("PM\u2082\u2009\u00B5 (µg m$^{-3}$)")
    plt.title("PM\u2082\u2009\u00B5 Box-Plot")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()
```

### 8.2.5 Wind-Speed vs PM₂.₅ (Scatter + Regression)

```python
import numpy as np
from numpy.polynomial.polynomial import polyfit

def plot_scatter(df, x="wind_mps", y="pm25",
                 path="figs/wind_vs_pm25.png"):
    plt.figure(figsize=(5,4))
    plt.scatter(df[x], df[y], s=10, alpha=.6)
    b0, b1 = polyfit(df[x], df[y], 1)
    xs = np.linspace(df[x].min(), df[x].max(), 100)
    plt.plot(xs, b0 + b1*xs, linewidth=2)
    r2 = np.corrcoef(df[x], df[y])[0,1]**2
    plt.text(.05,.95, f"R²={r2:.2f}", transform=plt.gca().transAxes)
    plt.xlabel("Wind speed (m s$^{-1}$)")
    plt.ylabel("PM\u2082\u2009\u00B5 (µg m$^{-3}$)")
    plt.title("Wind Speed vs PM\u2082\u2009\u00B5")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()
```

---

## **8.3 Turning Plots into Prefect Artifacts**

```python
from prefect import task
from prefect.artifacts import create_link_artifact, create_table_artifact
from pathlib import Path
import pandas as pd

@task
def publish_artifacts(img_dir="figs"):
    # upload plots
    for png in Path(img_dir).glob("*.png"):
        create_link_artifact(key=png.stem, link=png.as_uri(),
                             description="EDA graphic")
        
@task
def stats_table(df):
    tbl = df[["pm25","temp_c","rh_pct","wind_mps"]].describe().T
    create_table_artifact(key="summary", table=tbl)
```

Artifacts appear under the run’s **Artifacts** tab and remain linked forever—ideal for auditors.

---

## **8.4 Prefect Sub-Flow: `eda_pm25_flow`**

```python
from prefect import flow, get_run_logger

@flow(name="eda-pm25", log_prints=True)
def eda_pm25_flow(branch="main"):
    df = load_pm25(branch)
    plot_coverage(df)
    plot_timeseries(df)
    plot_hist(df)
    plot_box(df)
    plot_scatter(df)

    publish_artifacts()
    stats_table(df)
    get_run_logger().info("EDA ✅ completed")
```

Add this call at the end of `ingest_clean_flow` **or** deploy it on its own schedule.

---

## **8.5 README Integration**

After the first run, copy images out of the container (or mount a volume) and link with *relative paths*:

```markdown
## PM₂.₅ Exploratory Analysis

**Coverage – 24 h check**

<img src="figs/coverage.png" alt="Hourly coverage" width="600"/>

**Relationship between wind and PM₂.₅**

<img src="figs/wind_vs_pm25.png" alt="Wind vs PM2.5" width="500"/>
```

> Because paths are relative, GitHub renders them online **and** they still show up if the repo is zip-downloaded and opened offline.

---

## **8.6 Accessibility & Style Rules**

| Rule                                  | Why                        |
| ------------------------------------- | -------------------------- |
| Use **Tab10** or greyscale palette    | Colour-blind safe          |
| Minimum 10 pt axis labels             | Legible in presentations   |
| `plt.tight_layout()` before `savefig` | Prevent clipping           |
| Descriptive alt-text in README        | Screen-reader friendliness |

---

## **8.7 Iterating – EDA ↔ Cleaning Loop**

*Example:* coverage plot reveals missing data between 03:00-04:00.

1. Investigate raw API: maybe a rate-limit; adjust retry logic.
2. Re-run `ingest_clean_flow` for that day (branch `etl/2025-05-19`).
3. Merge to `main`, re-run `eda_pm25_flow`; bar is now full.

This iterative refinement is why EDA lives **inside Prefect**—dashboards update automatically.

---

## **8.8 Minimal Image Footprint**

All plots use **matplotlib only**, keeping the Docker layer < 80 MB.  Avoid seaborn/plotly in production; they balloon image size and bring extra dependencies.

---

## **8.9 Summary**

* **Coverage, distribution, outliers, and basic correlations** are now visible in every run.
* **Artifacts** preserve graphics and stats—no more lost screenshots.
* The insights (e.g., strong negative slope of wind vs PM₂.₅) directly inform **feature selection** for the regression pipeline you will build in Chapter 9.

With data understanding locked in you’re ready to construct the **baseline machine-learning model** that quantifies and predicts PM₂.₅ drivers.
