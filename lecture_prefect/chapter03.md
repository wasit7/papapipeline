# **Chapter 3: Prefect Server**

## **3.1 Introduction to Prefect Orchestration**

### 3.1.1 Prefect’s Evolution
- **Prefect 1.x** introduced the concept of a backend (Cloud or Core) to manage flows.  
- **Prefect 2.0+** (also often called **Prefect Orion**) simplified and modernized the interface, providing:
  - A new UI at a local or cloud-hosted endpoint  
  - An API for deployments, flow runs, and artifacts  
  - A more flexible, Pythonic approach to flows and tasks  

### 3.1.2 Self-Hosted vs. Prefect Cloud
- **Prefect Cloud**: Hosted service by Prefect, no need to manage servers; usage-based billing.  
- **Prefect Server** (self-hosted): Run your own orchestration server on-prem or in the cloud. Offers full control over data and infrastructure, but you maintain all services (database, server containers, etc.).

---

## **3.2 Overview of Prefect Server Components**

1. **Prefect API / UI**  
   - Provides a **web interface** (the Prefect Orion UI) for viewing flows, runs, deployments, logs, and schedules.  
   - Runs on **port 4200** by default in a local environment.  

2. **Database**  
   - Stores information about flows, deployments, schedules, and state transitions.  
   - **PostgreSQL** is commonly used in production environments due to reliability and concurrency support.

3. **Network / Configuration**  
   - Prefect Server processes connect to the database.  
   - Workers, the CLI, or any other client communicate with the server via `PREFECT_API_URL`.  

---

## **3.3 Starting the Prefect Server**

### 3.3.1 Local CLI Approach
If you have Prefect installed locally, you can do:
```bash
prefect server start --host 0.0.0.0
```
- By default, the UI is served at `http://127.0.0.1:4200`.
- You may optionally specify `--port <PORT>` if you need a different port.

### 3.3.2 Docker-Based Approach
Often, Prefect Server is run as a **Docker service**. For instance, in a `docker-compose.yml`:
```yaml
services:
  prefect-server:
    image: prefecthq/prefect:3-latest
    command: prefect server start --host 0.0.0.0
    ports:
      - "4200:4200"
    environment:
      - PREFECT_SERVER_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect
    depends_on:
      - postgres
```
- **`command: prefect server start --host 0.0.0.0`** exposes the service to external clients.  
- **`PREFECT_SERVER_DATABASE_CONNECTION_URL`** points the Prefect Server to the Postgres database running in another container named `postgres`.  
- **`depends_on: - postgres`** ensures Docker starts Postgres before the Prefect server.

---

## **3.4 Database Configuration**

### 3.4.1 Why PostgreSQL?
- **Postgres** is well-supported, efficient, and stable for handling orchestration metadata (e.g., flow states, schedules).  
- Prefect’s default connection string format is:
  ```bash
  postgresql+asyncpg://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>
  ```
  - Example: `postgresql+asyncpg://prefect:prefect@postgres:5432/prefect`.

### 3.4.2 Named Volumes for Persistence
To ensure your database contents aren’t lost on container restarts:
```yaml
volumes:
  postgres_data:

services:
  postgres:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=prefect
      - POSTGRES_PASSWORD=prefect
      - POSTGRES_DB=prefect
    volumes:
      - postgres_data:/var/lib/postgresql/data
```
This volume (`postgres_data`) persists all data stored within the database across container rebuilds.

---

## **3.5 Prefect API and Environment Variables**

### 3.5.1 `PREFECT_API_URL`
- Tells **Prefect clients** (CLI, workers, etc.) where to find the **API endpoint**.
- Example: `PREFECT_API_URL=http://prefect-server:4200/api` when using Docker Compose.  

### 3.5.2 `PREFECT_SERVER_DATABASE_CONNECTION_URL`
- Instructs **Prefect Server** on how to connect to the underlying database.  

### 3.5.3 Additional Configuration
Other environment variables or CLI options can control aspects like logging level, telemetry, etc. The main two for a basic setup are the API URL and the database connection URL.

---

## **3.6 Interacting with the Prefect Server**

### 3.6.1 Web UI
Once the server is running (e.g., `http://localhost:4200`):
1. **Deployments**: Lists all available flows and deployment configurations.  
2. **Work Pools**: Manage worker pools that pick up and execute flow runs.  
3. **Flow Runs**: Shows active, scheduled, or finished runs along with logs and status.  
4. **Schedules**: Review cron or interval-based schedules for each deployed flow.

### 3.6.2 Command-Line Interface
- **`prefect deployment ls`** (list registered deployments)  
- **`prefect deployment run <deployment-name>`** (manually trigger a flow run)  
- **`prefect logs`** (view recent logs for flow runs)  
- **`prefect server start`** (start local server for quick usage)

### 3.6.3 Checking Health
A **health endpoint** is often available at `/api/health`:
```bash
curl http://localhost:4200/api/health
# {"status":"healthy"} if everything is fine
```
In Docker Compose, this might be used in a **healthcheck**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:4200/api/health || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 10
```

---

## **3.7 Common Issues and Debugging**

1. **Database Connection Errors**  
   - Check `PREFECT_SERVER_DATABASE_CONNECTION_URL` for correct host, user, and password.  
   - Ensure `postgres` container is running before the Prefect server tries to connect.

2. **Port Conflicts**  
   - If something else is running on port `4200`, you may need to change the exposed port in `docker-compose.yml` or CLI arguments (e.g., `-p 4201:4200`).

3. **Pending or Stuck Flow Runs**  
   - Verify that the **Prefect worker** or **Work Pool** is running and able to connect to the server (via `PREFECT_API_URL`).

4. **Slow UI**  
   - Might indicate insufficient resources for the Postgres container or the server container. Increase CPU/memory as needed.

---

## **3.8 Best Practices for Self-Hosted Prefect Server**

1. **Use a Production-Grade Database**  
   - PostgreSQL with persistent volumes is strongly recommended.  
2. **Security and Access Control**  
   - Restrict access to the Prefect UI and API. Consider using SSL/TLS if exposing it outside local networks.  
3. **Regular Backups**  
   - Since all orchestration data (schedules, run states, logs) is in Postgres, schedule routine database backups.  
4. **Scaling and High Availability**  
   - For higher loads or critical environments, place the Prefect Server and Postgres on robust infrastructure.  
   - Replicate or cluster Postgres if you need high availability.

---

## **3.9 Summary**

In this chapter, you’ve learned about the **Prefect Server**—the backbone of your self-hosted Prefect environment. Key points include:

- **API & UI**: The server provides an interface to manage and visualize flow runs, schedules, and deployments.  
- **Database**: Postgres is commonly paired with Prefect Server to store orchestration metadata securely.  
- **Configuration**: `PREFECT_API_URL` and `PREFECT_SERVER_DATABASE_CONNECTION_URL` are essential environment variables for connecting your workers, CLI, and server.  
- **Health & Debugging**: Monitoring port 4200 and the `/api/health` endpoint ensures your server is responsive.

Next, in **Chapter 4**, we’ll dive into the **Prefect Worker**. You’ll see how workers register themselves with the server, pick up scheduled flows from work pools, and execute tasks in parallel. Understanding the server–worker interaction is crucial for building reliable data pipelines in Prefect.