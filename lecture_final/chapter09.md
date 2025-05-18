# **Chapter 9: Baseline Machine-Learning Pipelines**

*Case Study – Predicting Hourly PM₂.₅ Concentration*

The cleaned, version-controlled dataset that now lives in lakeFS contains **hourly air-quality observations** for Bangkok:

```text
timestamp, pm25, temp_c, rh_pct, wind_mps, no2_ppb, o3_ppb, site_id
2025-05-19T00:00:00+07:00, 21.4, 29.3, 78, 2.1, 15, 12, A
...
```

Our goal is to build a **baseline regression model** that explains (and predicts) PM₂.₅ using meteorological and co-pollutant features.  This chapter walks through the full workflow—**feature engineering → linear model → evaluation → model artifactory**—inside a Prefect flow so that retraining can run every night.

---

## **9.0 Learning Outcomes**

1. Select explanatory variables and craft *lag features* for a univariate target.
2. Assemble an **`sklearn.pipeline`** with `StandardScaler` + `LinearRegression`.
3. Log MAE & R² to the Prefect UI; store a confusion-free scatter plot.
4. Serialise the model (`joblib`) to a **lakeFS branch** and merge only on success.
5. Schedule retraining via a cron deployment (`0 2 * * *`).
6. Interpret regression coefficients to discuss drivers of PM₂.₅.

---

## **9.1 Feature Selection & Engineering**

| Raw column          | Rationale                               | Engineering step      |
| ------------------- | --------------------------------------- | --------------------- |
| `temp_c`            | Inversion layers affect dispersion      | Keep as is            |
| `rh_pct`            | High RH can trap particulates           | Keep                  |
| `wind_mps`          | Ventilation; expect **negative** coeff. | Keep                  |
| `no2_ppb`, `o3_ppb` | Traffic & photochemistry proxies        | Keep                  |
| `pm25_lag1`         | Autocorrelation hour‐to-hour            | `df["pm25"].shift(1)` |
| `pm25_lag24`        | Daily periodicity                       | `shift(24)`           |
| `site_id`           | Fixed-effects per station               | One-hot encode        |

We deliberately keep the baseline *simple*: no interaction terms, no tree models.

---

## **9.2 Loading & Preparing Data (Prefect Task)**

```python
from prefect import task
import pandas as pd

@task
def load_features(branch="main", repo="project"):
    df = load_curated(branch)                               # from Ch. 8 helper
    df = df.sort_values("timestamp")

    # Lag features
    df["pm25_lag1"]  = df["pm25"].shift(1)
    df["pm25_lag24"] = df["pm25"].shift(24)

    # Drop first 24 rows with NaNs from lagging
    df = df.dropna(subset=["pm25_lag1", "pm25_lag24"])

    # One-hot encode site_id
    df = pd.get_dummies(df, columns=["site_id"], drop_first=True)

    X = df.drop(columns=["pm25", "timestamp"])
    y = df["pm25"]
    return X, y
```

---

## **9.3 Building the Baseline Model**

### 9.3.1 Scikit-learn Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

def build_pipeline():
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("reg",   LinearRegression())
        ]
    )
```

### 9.3.2 Train–Test Split

```python
from sklearn.model_selection import train_test_split

@task
def train_baseline(X, y, test_size=0.2, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, shuffle=False
    )
    pipe = build_pipeline().fit(X_train, y_train)
    return pipe, X_test, y_test
```

`shuffle=False` preserves temporal order so the model is not trained on future data.

---

## **9.4 Evaluation & Logging**

```python
from sklearn.metrics import mean_absolute_error, r2_score
from prefect.artifacts import create_link_artifact
import matplotlib.pyplot as plt
import joblib, uuid

@task
def evaluate_model(pipe, X_test, y_test):
    y_pred = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)
    get_run_logger().info({"MAE": mae, "R2": r2})

    # Scatter plot
    fig_path = f"figs/pred_vs_obs_{uuid.uuid4().hex[:6]}.png"
    plt.figure(figsize=(5,5))
    plt.scatter(y_test, y_pred, alpha=0.6, s=10)
    plt.plot([y_test.min(), y_test.max()],
             [y_test.min(), y_test.max()], 'k--')
    plt.xlabel("Observed PM2.5"); plt.ylabel("Predicted PM2.5")
    plt.title(f"Pred vs Obs – R²={r2:.2f}")
    plt.tight_layout(); plt.savefig(fig_path, dpi=120); plt.close()
    create_link_artifact(key="pred_vs_obs", link=fig_path)

    return mae, r2, y_pred
```

---

## **9.5 Persisting the Model to lakeFS**

```python
from pathlib import Path, PurePosixPath

@task
def save_model(pipe, execution_date, repo="project"):
    branch = f"model/{execution_date}"
    fname  = f"linreg_pm25_{execution_date}.pkl"
    joblib.dump(pipe, fname)

    # Upload to lakeFS
    key = f"{branch}/models/{fname}"
    lakefs_s3().upload_file(Filename=fname, Bucket=repo, Key=key)

    # Commit & merge to main only if MAE < 10 µg/m³
    _commit(branch, f"Model {fname}")        # tiny helper, same as Ch. 7
    _merge(branch, "main")                   # merge models into main
    return f"s3://{repo}/{key}"
```

> **Policy**:  we merge models to `main` only when evaluation passes a threshold—this prevents accidentally promoting a worse model.

---

## **9.6 Full Prefect Flow**

```python
from datetime import date
from prefect import flow

@flow(name="pm25-baseline", log_prints=True)
def pm25_baseline_flow(execution_date: str = date.today().isoformat()):
    X, y        = load_features()
    pipe, Xt, yt = train_baseline(X, y)
    mae, r2, _  = evaluate_model(pipe, Xt, yt)

    if mae < 10:         # µg/m³ threshold for promotion
        model_uri = save_model(pipe, execution_date)
        get_run_logger().info(f"Model saved to {model_uri}")
    else:
        raise ValueError(f"MAE {mae:.2f} >= 10; model not saved")

if __name__ == "__main__":
    pm25_baseline_flow.serve(
        name="daily-pm25-retrain",
        work_pool_name="ml-pool",
        cron="0 2 * * *"     # run at 02:00 daily
    )
```

---

## **9.7 Interpreting Coefficients**

After a successful run:

```python
coef = pipe.named_steps["reg"].coef_
for feat, val in zip(X.columns, coef):
    print(f"{feat:<12} {val: .2f}")
```

Typical baseline insights:

| Feature      | Sign  | Interpretation                  |
| ------------ | ----- | ------------------------------- |
| `wind_mps`   | **–** | Higher wind dilutes PM₂.₅       |
| `temp_c`     | +     | Hot stable layers may trap smog |
| `pm25_lag1`  | +     | Hour-to-hour persistence        |
| `pm25_lag24` | +     | Daily cycle                     |

These qualitative findings feed into the **final presentation** (Chapter 11).

---

## **9.8 Scheduled Retraining**

Why nightly?

| Reason                        | Impact                                  |
| ----------------------------- | --------------------------------------- |
| Sensor drift (new site added) | Model automatically absorbs             |
| Seasonal change               | Captures monsoon vs dry season patterns |
| Data quality fix              | Fresh run trains on corrected dataset   |

Because Prefect schedule metadata lives with the deployment, updates are a single CLI:

```bash
prefect deployment update pm25-baseline/daily-pm25-retrain \
  --cron "0 */6 * * *"   # move to every 6 hours if needed
```

---

## **9.9 Summary & Next Steps**

* You built a **deterministic, automated baseline**:

  * Feature engineering in a task
  * `sklearn.pipeline` with standard scaling
  * Metrics logged & plotted as artifacts
  * Model saved only when MAE target met

* This satisfies the rubric’s ML requirement (5 pts) and sets a reference point for any fancier model you may add (random forest, XGBoost, etc.).

* The **interpretability** of linear regression also provides concrete talking points for policymakers who care *why* PM₂.₅ changes, not just *how much* it will be.

With the model artefacts stored and version-controlled, Chapter 10 will push the entire stack into a CI/CD pipeline so new data, new features, and new models flow to production with a single pull-request.
