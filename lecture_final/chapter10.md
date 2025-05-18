# **Chapter 10: Productionisation & CI/CD**

*From “works on my machine” to **repeatable—in-one-command** deployment*

Up to now every piece—data-quality tasks, ingest–clean flow, EDA flow, PM₂.₅ baseline model—runs correctly in a dev container.  This chapter turns those notebooks and scripts into a **fully automated delivery pipeline** so that:

* a single `git push` triggers lint → test → Docker build → Prefect deployment,
* the stack can be spun up on any server with one command: `docker compose up --build`,
* promotion from *dev* to *stage* to *prod* is a label flip—not a copy-paste job,
* incident detection and rollback are **two clicks**.

---

## **10.0 Component Inventory**

| Layer          | What is shipped?                                       | Delivery artefact          |
| -------------- | ------------------------------------------------------ | -------------------------- |
| **App images** | `prefect-worker`, `jupyter-lakefs`, custom `ml-worker` | Docker images (GHCR)       |
| **Infra**      | Prefect Server + Postgres, MinIO + lakeFS, Loki        | `docker-compose.prod.yml`  |
| **Code**       | Flow scripts, schema YAML, notebooks                   | Git repository             |
| **Models**     | `linreg_pm25_YYYY-MM-DD.pkl`                           | lakeFS `model/main` branch |

---

## **10.1 Multi-Stage Docker Builds**

### 10.1.1 `Dockerfile.worker`

```dockerfile
# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim
LABEL maintainer="dsi321@tu.ac.th"
ENV PYTHONUNBUFFERED=1 \
    PREFECT_API_URL=http://prefect-server:4200/api

# copy deps from builder image
COPY --from=builder /install /usr/local
# copy only source code needed by flows
COPY flows/ /opt/prefect/flows/

ENTRYPOINT ["prefect", "worker", "start", "-p", "etl-pool"]
```

*Result:* < 150 MB image, reproducible because **`requirements.txt` is pinned** (generated via `pip-compile`).

> **Best practice** – Tag worker images `worker:prefect-2.21-2025-05-19` (Prefect + build date) for semantic rollback.

---

## **10.2 Docker Compose for Production**

```yaml
# docker-compose.prod.yml
version: "3.9"

services:

  prefect-server:
    image: prefecthq/prefect:2.21-python3.11
    command: prefect server start
    ports: ["4200:4200"]
    environment:
      PREFECT_UI_URL: http://localhost:4200

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: prefect
      POSTGRES_PASSWORD: prefect
    volumes: ["pgdata:/var/lib/postgresql/data"]

  lakefs:
    image: treeverse/lakefs:1.7
    ports: ["8000:8000"]
    environment:
      LAKEFS_AUTH_ENCRYPT_SECRET_KEY: "changeme"
    depends_on: [minio]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: lakefs
      MINIO_ROOT_PASSWORD: lakefs123
    ports: ["9000:9000", "9001:9001"]
    volumes: ["minio:/data"]

  loki:
    image: grafana/loki:3.0
    command: -config.file=/etc/loki/local-config.yaml
    ports: ["3100:3100"]

  prefect-worker:
    image: ghcr.io/your-org/worker:latest
    depends_on: [prefect-server]
    environment:
      LAKEFS_ENDPOINT: http://lakefs:8000
      LAKEFS_ACCESS_KEY: lakefs
      LAKEFS_SECRET_KEY: lakefs123
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"

volumes:
  pgdata:
  minio:
```

> **One-command spin-up**
>
> ```bash
> docker compose -f docker-compose.prod.yml up --build -d
> ```

Everything—server, object storage, Git-for-data, log aggregation—starts ready for action.

---

## **10.3 GitHub Actions Workflow**

`.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [ main ]

jobs:

  build-test-lint:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with: { python-version: '3.11' }

    - name: Install deps
      run: |
        pip install -r requirements-dev.txt
        pip install -r requirements.txt

    - name: Lint (ruff)
      run: ruff flows/ --output-format=github

    - name: Unit tests (pytest)
      run: pytest -q

  build-and-push-image:
    needs: build-test-lint
    runs-on: ubuntu-latest
    permissions: { packages: write, contents: read }

    steps:
    - uses: actions/checkout@v4
    - name: Log in to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build & push
      uses: docker/build-push-action@v5
      with:
        push: true
        tags: ghcr.io/your-org/worker:${{ github.sha }}
        file: Dockerfile.worker

  apply-prefect-deployment:
    needs: build-and-push-image
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4
    - name: Prefect Login
      run: prefect cloud login --key "${{ secrets.PREFECT_API_KEY }}"
    - name: Update deployment
      run: |
        prefect deployment update ingest-clean/daily-ingest \
          --image ghcr.io/your-org/worker:${{ github.sha }}
```

Key points

* **Gate 1** – lint & tests must pass.
* **Gate 2** – only then build + push image.
* **Gate 3** – Prefect deployment “daily-ingest” is patched to use the new image tag.

A **build-status badge** goes into `README.md`:

```markdown
![CI](https://github.com/your-org/pm25/actions/workflows/ci.yml/badge.svg)
```

---

## **10.4 Environment Promotion with Work-Pool Labels**

```
etl-pool-dev   → label: dev
etl-pool-stage → label: stage
etl-pool-prod  → label: prod
```

* In the Prefect UI, duplicate the *daily-ingest* deployment:

  * Version 1 → dev pool (auto)
  * Version 2 → stage pool (on approval)
  * Version 3 → prod pool (after UAT sign-off)

Changing pools is just:

```bash
prefect deployment update ingest-clean/daily-ingest \
    --work-pool etl-pool-prod
```

---

## **10.5 Observability**

### 10.5.1 Health-Check Task

```python
@task(retries=2, retry_delay_seconds=30)
def health_check():
    import httpx
    r = httpx.get("https://aqicn.org/city/bangkok-air-quality/")
    if r.status_code != 200:
        raise ValueError("Source API unreachable")
```

Place this task at the top of any flow.  If it fails, the flow becomes `FAILED`, Slack is pinged.

### 10.5.2 Slack Alert Block

```bash
prefect block create --type slack-webhook --name qa-alerts
# paste webhook URL
```

Then in deployment schedule:

```yaml
interruptible: true
notifications:
  - block_document_id: slack-webhook/qa-alerts
    tags: [ "SLACK" ]
    state_names: [ "Failed", "Crashed" ]
```

### 10.5.3 Loki Log Search

With the logging driver wired to Loki, query:

```
{container="prefect-worker"} |= "Validation failed"
```

to instantly find flow-runs that broke data-quality contracts.

---

## **10.6 Rollback & Disaster Recovery**

Scenario: new image causes data-quality drop < 90 %.

1. **Stop deploy** in Prefect UI (one click).
2. Re-tag previous good image (e.g., `worker:prev`) and redeploy:

   ```bash
   prefect deployment update ingest-clean/daily-ingest \
       --image ghcr.io/your-org/worker:prev
   ```
3. Because lakeFS keeps every commit branch, you can `lakefs diff --parent main etl/2025-05-27` to inspect exactly what bad data came in.

---

## **10.7 One-Command Spin-Up Script**

`make deploy-prod`

```makefile
.PHONY: deploy-prod
deploy-prod:
	docker compose -f docker-compose.prod.yml pull
	docker compose -f docker-compose.prod.yml up --build -d
```

A new teammate (or grader) runs a single command and sees Prefect UI at `http://localhost:4200`, lakeFS at `http://localhost:8000`, Loki at `:3100`, all pre-wired.

---

## **10.8 Checklist for the Rubric**

| Checklist item                        | Where satisfied                                   |
| ------------------------------------- | ------------------------------------------------- |
| **Run entire stack with one command** | `docker compose up --build`                       |
| **Version-pinned dependencies**       | `requirements.txt`, multi-stage Dockerfile        |
| **CI pipeline**                       | `ci.yml` sections: lint, tests, image, deployment |
| **Promotion path**                    | Work-pool labels dev → stage → prod               |
| **Rollback strategy**                 | Semantic image tags + lakeFS data commits         |
| **Health monitoring**                 | Slack webhook + Loki logs                         |

---

## **10.9 Summary**

Your pipeline is now:

1. **Containerised** – every dependency frozen.
2. **Continuously integrated** – push → lint/test/build/tag → Prefect update.
3. **Observable** – metrics, logs, alerts.
4. **Rollback-ready** – one command restores last good version.

With CI/CD in place, Chapter 11 focuses on **integration rehearsals, peer review, and the final demo**, confident that the pipeline will behave the same on the instructor’s machine as on yours.
